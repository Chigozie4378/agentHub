from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio

from app.shared.db import get_db
from app.shared import sse
from app.conversations.schemas import (
    ConversationCreate, ConversationUpdate, ConversationOut, ConversationList,
    MessageCreate, MessageOut, MessageList
)
from app.conversations.service import (
    create_conversation, get_conversation, list_conversations, update_conversation, soft_delete_conversation,
    create_message
)
from app.runs.service import create_run, add_step, finish_run

from app.shared.guard import bump_for_user



from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.conversations.models import Message
    from app.runs.models import Run


router = APIRouter(prefix="/conversations", tags=["Conversations"])

# TODO: replace with real auth; for now a stubbed user id
def current_user_id() -> str:
    return "demo-user"

@router.post("", response_model=ConversationOut, status_code=201)
def create_conv(payload: ConversationCreate, db: Session = Depends(get_db)):
    conv = create_conversation(db, current_user_id(), payload)
    return conv

@router.get("", response_model=ConversationList)
def list_conv(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, description="ISO8601 created_at of last item from previous page"),
    db: Session = Depends(get_db),
):
    items, next_cursor = list_conversations(db, current_user_id(), limit, cursor)
    return {"items": items, "next_cursor": next_cursor}

@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conv(conversation_id: str, db: Session = Depends(get_db)):
    conv = get_conversation(db, current_user_id(), conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv

@router.patch("/{conversation_id}", response_model=ConversationOut)
def patch_conv(conversation_id: str, payload: ConversationUpdate, db: Session = Depends(get_db)):
    conv = update_conversation(db, current_user_id(), conversation_id, payload)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv

@router.delete("/{conversation_id}", status_code=204)
def delete_conv(conversation_id: str, db: Session = Depends(get_db)):
    ok = soft_delete_conversation(db, current_user_id(), conversation_id)
    if not ok:
        raise HTTPException(404, "Conversation not found")
    return

@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=202)
async def post_message(conversation_id: str, payload: MessageCreate, db: Session = Depends(get_db)):
    uid = current_user_id()
    msg = create_message(db, uid, conversation_id, payload.text, payload.attachments)
    if not msg:
        raise HTTPException(404, "Conversation not found")

    text = payload.text.strip().lower()

    # Convenience: allow "yes"/"no" to confirm/cancel latest pending run
    from app.runs.service import get_latest_pending, confirm_run, cancel_run, finish_run, add_step, create_run
    pending = get_latest_pending(db, conversation_id)

    if text in ("yes", "y") and pending:
        # execute the stored payload now
        run = confirm_run(db, pending.id)
        await sse.publish(conversation_id, "confirmation", {"run_id": run.id, "status": "confirmed"})
        asyncio.create_task(_execute_pending_payload(conversation_id, run, db, uid))
        return _message_out(msg)


    if text in ("no", "n", "cancel") and pending:
        cancel_run(db, pending.id)
        await sse.publish(conversation_id, "confirmation", {"run_id": pending.id, "status": "cancelled"})
        return _message_out(msg)

    # No pending confirmation or not yes/no -> treat as new request
    # If attachments exist, keep Phase-0 inline bundle behavior (chat-only)
    if payload.attachments and not text.startswith("!!"):
        asyncio.create_task(_execute_chat_with_files(conversation_id, uid, payload, db))
        return _message_out(msg)

    # Detect tool commands and ask for confirmation
    if text.startswith("!!browse"):
        # parse url + optional actions json
        import json
        parts = payload.text.split(" ", 2)
        url = parts[1] if len(parts) > 1 else ""
        actions = None
        if len(parts) == 3:
            try: actions = json.loads(parts[2]).get("actions")
            except Exception: actions = None
        plan = ["plan_browser", "open_page", "capture"]
        run = create_run(db, conversation_id, mode="task", plan=plan, needs_confirmation=True,
                         pending_payload={"tool":"browser","url":url,"actions":actions})
        # notify stream
        await sse.publish(conversation_id, "reasoning_plan", {"steps": plan, "run_id": run.id})
        await sse.publish(conversation_id, "confirm_needed", {
            "run_id": run.id,
            "summary": f"Open {url} and take a screenshot.",
            "how_to_confirm": {"rest":"POST /runs/{run_id}/confirm", "chat":"reply 'yes'"},
        })
        from app.runs.service import mark_awaiting_confirmation
        mark_awaiting_confirmation(db, run.id)
        return _message_out(msg)

    if text.startswith("!!email"):
        cmd = payload.text[len("!!email"):].strip()
        plan = ["compose_email", "dry_run_save"]
        run = create_run(db, conversation_id, mode="task", plan=plan, needs_confirmation=True,
                         pending_payload={"tool":"email","command":cmd})
        await sse.publish(conversation_id, "reasoning_plan", {"steps": plan, "run_id": run.id})
        await sse.publish(conversation_id, "confirm_needed", {
            "run_id": run.id,
            "summary": f"Draft an email ({cmd})",
            "how_to_confirm": {"rest":"POST /runs/{run_id}/confirm", "chat":"reply 'yes'"},
        })
        from app.runs.service import mark_awaiting_confirmation
        mark_awaiting_confirmation(db, run.id)
        return _message_out(msg)

    # default: plain chat with optional files handled above
    asyncio.create_task(_execute_plain_chat(conversation_id, db))
    return _message_out(msg)

# --- helpers below (paste into same file) ---

def _message_out(msg: "Message") -> MessageOut:
    return MessageOut(
        id=msg.id, conversation_id=msg.conversation_id, role=msg.role,
        text=msg.text, attachments=msg.attachments, created_at=msg.created_at,
    )

async def _execute_chat_with_files(conversation_id: str, uid: str, payload: MessageCreate, db: Session):
    from app.files.service import get_file_many, inline_bundle_for_files
    from app.runs.service import create_run, add_step, finish_run
    files = get_file_many(db, uid, payload.attachments)
    bundle = inline_bundle_for_files(files)
    run = create_run(db, conversation_id, mode="chat", plan=["receive_attachments","parse_inline_context","generate_answer"])
    for fid in payload.attachments:
        await sse.publish(conversation_id, "attachment_received", {"file_id": fid})
    await sse.publish(conversation_id, "attachment_parsed", {
        "count": len(files),
        "sources": [{"file_id": s["file_id"], "filename": s["filename"]} for s in bundle["sources"]]
    })
    await sse.publish(conversation_id, "context_ready", {"sources": bundle["sources"]})
    text = "I read your files. " + (bundle["text"][:400].replace("\n", " ") + "..." if bundle["text"] else "No readable text found.")
    for tok in text.split(" "):
        await sse.publish(conversation_id, "token", {"text_chunk": tok + " "})
    await sse.publish(conversation_id, "final_answer", {"text": text, "citations": []})
    finish_run(db, run.id, status="completed")

async def _execute_plain_chat(conversation_id: str, db: Session):
    from app.runs.service import create_run, finish_run
    run = create_run(db, conversation_id, mode="chat", plan=["generate_answer"])
    await sse.publish(conversation_id, "reasoning_plan", {"steps": ["generate_answer"]})
    text = "Message received. (Planner confirmation enabled for tools.)"
    for tok in text.split(" "):
        await sse.publish(conversation_id, "token", {"text_chunk": tok + " "})
    await sse.publish(conversation_id, "final_answer", {"text": text, "citations": []})
    finish_run(db, run.id, status="completed")

async def _execute_pending_payload(conversation_id: str, run: "Run", db: Session, uid: str):
    from app.runs.service import add_step, finish_run
    payload = run.pending_payload
    tool = payload.get("tool")
    if tool == "browser":
        from app.tools.browser.service import browse
        out = await browse(payload.get("url",""), payload.get("actions"))
        await sse.publish(conversation_id, "artifact_ready", {"kind": "screenshot", "path": out.get("screenshot_path")})
        await sse.publish(conversation_id, "final_answer", {
            "text": f"Opened {payload.get('url')} and captured a screenshot.",
            "artifacts": [out.get("screenshot_path")],
        })

        # bump guard usage for this confirmed tool run
        bump_for_user(db, uid, token_cost=8000)
        finish_run(db, run.id, status="completed")
        return
    if tool == "email":
        from app.tools.email.service import draft_email
        cmd = payload.get("command","")
        parts = dict(p.split(":",1) for p in cmd.split("|") if ":" in p)
        to = parts.get("to","").strip(); subject = parts.get("subject","").strip(); body = parts.get("body","").strip()
        out = draft_email(to, subject, body)
        await sse.publish(conversation_id, "artifact_ready", {"kind":"email_draft", "path": out["artifact_path"]})
        await sse.publish(conversation_id, "final_answer", {"text": f"Drafted email to {to} (dry-run).", "artifact": out})
        
        # bump guard usage
        bump_for_user(db, uid, token_cost=3000)
        finish_run(db, run.id, status="completed")
        return
    # Unknown tool fallback
    await sse.publish(conversation_id, "final_answer", {"text": "Pending action not recognized."})
    finish_run(db, run.id, status="failed")


@router.get("/{conversation_id}/stream")
async def stream(conversation_id: str, request: Request):
    async def _gen():
        async for part in sse.sse_stream(conversation_id):
            # Client disconnected?
            if await request.is_disconnected():
                break
            yield part
    return StreamingResponse(_gen(), media_type="text/event-stream")