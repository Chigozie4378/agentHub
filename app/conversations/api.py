# Standard library
import asyncio
import json
from typing import TYPE_CHECKING

# FastAPI / Starlette
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session

# Shared infrastructure
from app.shared.db import get_db
from app.shared import sse
from app.shared.guard import bump_for_user  # guard wall usage counter

# Conversations
from app.conversations.schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationOut,
    ConversationList,
    MessageCreate,
    MessageOut,
    MessageList,
)
from app.conversations.service import (
    create_conversation,
    get_conversation,
    list_conversations,
    update_conversation,
    soft_delete_conversation,
    create_message,
)

# Runs
from app.runs.service import (
    create_run,
    add_step,
    finish_run,
)

# TYPE_CHECKING avoids runtime import cycles
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



# app/conversations/api.py  — replace the entire function below

async def _execute_pending_payload(conversation_id: str, run: "Run", db: Session):
    """
    Executes the canonical pending payload stored on the run.
    Expects run.pending_payload == {"name": <tool_name>, "args": {...}}
    Falls back to legacy shape if needed.
    Streams SSE events: artifact_ready, token, final_answer, etc.
    Also bumps guard-wall usage counters per successful tool execution.
    """
    from app.runs.service import finish_run, _normalize_pending_payload
    from app.shared.guard import bump_for_user  # <-- correct import
    uid = current_user_id()
    payload = run.pending_payload or {}

    # Normalize for safety (works for both legacy and canonical)
    name = payload.get("name")
    args = payload.get("args", {})
    if not name and "tool" in payload:
        name, args = _normalize_pending_payload(payload)

    try:
        # ---------------- Browser ----------------
        if name == "browser.screenshot":
            from app.tools.browser.service import browse  # async def browse(url, actions)
            out = await browse(args.get("url", ""), args.get("actions"))
            await sse.publish(conversation_id, "artifact_ready", {"kind": "screenshot", "path": out.get("screenshot_path")})
            await sse.publish(conversation_id, "final_answer", {
                "text": f"Opened {args.get('url')} and captured a screenshot.",
                "artifacts": [out.get("screenshot_path")],
            })
            bump_for_user(db, uid, token_cost=8000, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Email ----------------
        if name == "email.draft_send":
            from app.tools.email.service import draft_email  # def draft_email(to, subject, body, dry_run=True)
            to = (args.get("to") or "").strip()
            subject = (args.get("subject") or "").strip()
            body = (args.get("body") or "").strip()
            dry = bool(args.get("dry_run", True))
            out = draft_email(to, subject, body, dry_run=dry)
            if out.get("artifact_path"):
                await sse.publish(conversation_id, "artifact_ready", {"kind":"email_draft", "path": out["artifact_path"]})
            await sse.publish(conversation_id, "final_answer", {"text": f"Email {'drafted' if dry else 'sent'} to {to}.", "artifact": out})
            bump_for_user(db, uid, token_cost=3000, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- PDF ----------------
        if name == "pdf.generate":
            from app.tools.pdf.service import generate_pdf  # def generate_pdf(html=None, markdown=None, filename=None)
            out = generate_pdf(
                html=args.get("html"),
                markdown=args.get("markdown"),
                filename=args.get("filename")
            )
            await sse.publish(conversation_id, "artifact_ready", {"kind": "pdf", "path": out.get("pdf_path")})
            await sse.publish(conversation_id, "final_answer", {"text": f"Generated PDF {out.get('pdf_path')}.", "artifact": out})
            bump_for_user(db, uid, token_cost=2000, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- CSV ----------------
        if name == "csv.preview":
            from app.tools.csv.service import preview_csv  # def preview_csv(file_id, limit=50)
            out = preview_csv(file_id=args.get("file_id"), limit=args.get("limit") or 50)
            if out.get("normalized_csv_path"):
                await sse.publish(conversation_id, "artifact_ready", {"kind": "csv", "path": out["normalized_csv_path"]})
            await sse.publish(conversation_id, "final_answer", {
                "text": f"CSV preview: {len(out.get('rows', []))} rows. Headers: {', '.join(out.get('headers', []))}",
                "data": {"headers": out.get("headers"), "rows": out.get("rows")[:5]}
            })
            bump_for_user(db, uid, token_cost=1500, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Places ----------------
        if name == "places.search":
            from app.tools.places.service import search_places  # def search_places(q, near=None)
            out = search_places(q=args.get("q"), near=args.get("near"))
            await sse.publish(conversation_id, "final_answer", {
                "text": f"Built search links for '{out.get('query')}'.",
                "links": out.get("links", [])
            })
            bump_for_user(db, uid, token_cost=2000, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Web Search ----------------
        if name == "search.web":
            from app.tools.search.service import web_search  # def web_search(q)
            out = web_search(q=args.get("q", ""))
            await sse.publish(conversation_id, "final_answer", {
                "text": f"Search results for '{args.get('q','')}':",
                "links": out.get("links", [])
            })
            bump_for_user(db, uid, token_cost=2500, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Download ----------------
        if name == "download.fetch":
            from app.tools.download.service import fetch  # def fetch(url)
            out = fetch(args.get("url", ""))
            await sse.publish(conversation_id, "artifact_ready", {"kind": "file", "path": out.get("artifact_path")})
            await sse.publish(conversation_id, "final_answer", {"text": f"Downloaded file ({out.get('size')} bytes).", "artifact": out})
            bump_for_user(db, uid, token_cost=2000, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Summarize ----------------
        if name == "summarize.document":
            from app.tools.summarize.service import summarize_document  # def summarize_document(db, user_id, file_id, max_chars)
            out = summarize_document(db, uid, file_id=args.get("file_id"), max_chars=args.get("max_chars") or 800)
            await sse.publish(conversation_id, "final_answer", {"text": out.get("summary", ""), "meta": {"length": out.get("length")}})
            bump_for_user(db, uid, token_cost=3500, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Sentiment ----------------
        if name == "sentiment.analyze":
            from app.tools.sentiment.service import analyze_sentiment  # def analyze_sentiment(text)
            out = analyze_sentiment(text=args.get("text", ""))
            await sse.publish(conversation_id, "final_answer", {
                "text": f"Sentiment: {out.get('label')}",
                "scores": out.get("scores")
            })
            bump_for_user(db, uid, token_cost=1200, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Todos ----------------
        if name == "todos.create":
            from app.tools.todos.service import create_todo
            item = create_todo(uid, args.get("title",""), args.get("due_at"), args.get("labels") or [])
            await sse.publish(conversation_id, "final_answer", {"text": f"Todo created: {item['title']}", "item": item})
            bump_for_user(db, uid, token_cost=800, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        if name == "todos.list":
            from app.tools.todos.service import list_todos
            items = list_todos(uid, status=args.get("status"))
            await sse.publish(conversation_id, "final_answer", {"text": f"{len(items)} todo(s).", "items": items})
            bump_for_user(db, uid, token_cost=600, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        if name == "todos.update":
            from app.tools.todos.service import update_todo
            item = update_todo(uid, args.get("todo_id"), status=args.get("status"))
            await sse.publish(conversation_id, "final_answer", {"text": f"Todo updated: {item['id']}", "item": item})
            bump_for_user(db, uid, token_cost=700, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        if name == "todos.delete":
            from app.tools.todos.service import delete_todo
            ok = delete_todo(uid, args.get("todo_id"))
            await sse.publish(conversation_id, "final_answer", {"text": "Todo deleted." if ok else "Todo not found."})
            bump_for_user(db, uid, token_cost=500, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Notes ----------------
        if name == "notes.create":
            from app.tools.notes.service import create_note
            item = create_note(uid, args.get("text",""), args.get("tags") or [])
            await sse.publish(conversation_id, "final_answer", {"text": "Note saved.", "item": item})
            bump_for_user(db, uid, token_cost=700, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        if name == "notes.summarize":
            from app.tools.notes.service import summarize_notes
            out = summarize_notes(uid, tag=args.get("tag"), since=args.get("since"))
            await sse.publish(conversation_id, "final_answer", {"text": out.get("summary",""), "count": out.get("count",0)})
            bump_for_user(db, uid, token_cost=2500, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Reminders ----------------
        if name == "reminders.create":
            from app.tools.reminders.service import create_reminder
            item = create_reminder(uid, args.get("text",""), args.get("remind_at"))
            await sse.publish(conversation_id, "final_answer", {"text": "Reminder set.", "item": item})
            bump_for_user(db, uid, token_cost=1000, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Calendar ----------------
        if name == "calendar.create_event":
            from app.tools.calendar.service import create_event
            item = create_event(uid, **args)
            await sse.publish(conversation_id, "final_answer", {"text": f"Event created: {item['title']}", "item": item})
            bump_for_user(db, uid, token_cost=1500, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        if name == "calendar.update_event":
            from app.tools.calendar.service import update_event
            eid = args.pop("event_id", None)
            item = update_event(uid, eid, **args)
            await sse.publish(conversation_id, "final_answer", {"text": f"Event updated: {item['id']}", "item": item})
            bump_for_user(db, uid, token_cost=1200, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        if name == "calendar.delete_event":
            from app.tools.calendar.service import delete_event
            ok = delete_event(uid, args.get("event_id"))
            await sse.publish(conversation_id, "final_answer", {"text": "Event deleted." if ok else "Event not found."})
            bump_for_user(db, uid, token_cost=800, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        if name == "calendar.list_events":
            from app.tools.calendar.service import list_events
            items = list_events(uid, start=args.get("start"), end=args.get("end"))
            await sse.publish(conversation_id, "final_answer", {"text": f"{len(items)} event(s).", "items": items})
            bump_for_user(db, uid, token_cost=900, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        if name == "calendar.mark_date":
            from app.tools.calendar.service import mark_date
            out = mark_date(uid, date=args.get("date"), label=args.get("label"))
            await sse.publish(conversation_id, "final_answer", {"text": f"Marked {out['date']} as {out['label']}.", "marked": out})
            bump_for_user(db, uid, token_cost=600, tasks_inc=1)
            finish_run(db, run.id, status="completed"); return

        # ---------------- Unknown ----------------
        await sse.publish(conversation_id, "final_answer", {"text": f"Pending action not recognized: {name or payload}."})
        finish_run(db, run.id, status="failed")

    except Exception as e:
        await sse.publish(conversation_id, "final_answer", {"text": f"Tool failed: {type(e).__name__}: {e}"})
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