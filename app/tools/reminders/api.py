from fastapi import APIRouter
from pydantic import BaseModel
from .service import create_reminder

router = APIRouter(prefix="/tools/reminders", tags=["Tools: Reminders"])

def current_user_id() -> str:
    return "demo-user"

class ReminderIn(BaseModel):
    text: str
    remind_at: str

@router.post("")
def api_reminders_create(inb: ReminderIn):
    return create_reminder(current_user_id(), inb.text, inb.remind_at)
