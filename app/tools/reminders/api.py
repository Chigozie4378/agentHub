# app/tools/reminders/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import create_reminder

router = APIRouter(prefix="/tools/reminders", tags=["Tools: Reminders"])

def current_user_id() -> str: return "demo-user"

class ReminderIn(BaseModel):
    text: str
    remind_at: str

@router.post("/create")
def api_reminders_create(inb: ReminderIn, ctx=Depends(guard_gate("reminders"))):
    item = create_reminder(current_user_id(), inb.text, inb.remind_at)
    bump_after_tool(ctx, token_cost=1000)
    return ok(item)
