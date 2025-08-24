from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.shared.guard import guard_gate, bump_after_tool

router = APIRouter(prefix="/tools/reminders", tags=["Tools: Reminders"])

class ReminderCreate(BaseModel):
    text: str
    remind_at: str  # ISO8601

class ReminderItem(BaseModel):
    id: str
    text: str
    remind_at: str
    status: str = "scheduled"

_MEM: dict[str, ReminderItem] = {}

@router.post("", summary="Create reminder")
def create_reminder(body: ReminderCreate, ctx=Depends(guard_gate("reminders"))):
    import uuid
    rid = uuid.uuid4().hex
    item = ReminderItem(id=rid, text=body.text, remind_at=body.remind_at)
    _MEM[rid] = item
    # TODO: enqueue for delivery (Celery/Redis or external scheduler)
    bump_after_tool(ctx, token_cost=700)
    return {"ok": True, "id": rid, "item": item.model_dump()}
