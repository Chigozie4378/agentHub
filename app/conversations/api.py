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

    # Build plan
    plan = ["receive_attachments"]
    if payload.attachments:
        plan.append("parse_inline_context")
    plan.append("generate_answer")
    run = create_run(db, conversation_id=conversation_id, mode="chat", plan=plan)

    async def execute():
        idx = 0
        # emit attachment events
        for fid in payload.attachments:
            await sse.publish(conversation_id, "attachment_received", {"file_id": fid})
        bundle = None
        if payload.attachments:
            from app.files.service import get_file_many, inline_bundle_for_files
            files = get_file_many(db, uid, payload.attachments)
            bundle = inline_bundle_for_files(files)
            await sse.publish(conversation_id, "attachment_parsed", {
                "count": len(files),
                "sources": [{"file_id": s["file_id"], "filename": s["filename"]} for s in bundle["sources"]]
            })

        await sse.publish(conversation_id, "reasoning_plan", {"steps": plan})
        if bundle:
            await sse.publish(conversation_id, "context_ready", {"sources": bundle["sources"]})

        # Very simple Phase-0 “answer”: echo and brief stats from bundle
        if bundle and bundle["text"].strip():
            preview = bundle["text"][:400].replace("\n", " ")
            answer = (
                "I read your files. "
                f"Sources: {len(bundle['sources'])}. "
                f"Preview: {preview}..."
            )
        else:
            answer = "Message received. (Phase-0 demo: tools/RAG not invoked yet.)"

        # stream tokens
        for token in answer.split(" "):
            await sse.publish(conversation_id, "token", {"text_chunk": token + " "})
            add_step(db, run.id, idx, "token", {"text": token})
            idx += 1

        await sse.publish(conversation_id, "final_answer", {
            "text": answer,
            "citations": [{"file_id": s["file_id"]} for s in (bundle["sources"] if bundle else [])]
        })
        add_step(db, run.id, idx, "final", {"text": answer})
        finish_run(db, run.id, status="completed")

    asyncio.create_task(execute())

    return MessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        role=msg.role,
        text=msg.text,
        attachments=msg.attachments,
        created_at=msg.created_at,
    )

@router.get("/{conversation_id}/stream")
async def stream(conversation_id: str, request: Request):
    async def _gen():
        async for part in sse.sse_stream(conversation_id):
            # Client disconnected?
            if await request.is_disconnected():
                break
            yield part
    return StreamingResponse(_gen(), media_type="text/event-stream")