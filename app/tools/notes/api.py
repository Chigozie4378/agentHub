from fastapi import APIRouter
from pydantic import BaseModel
from .service import create_note, summarize_notes

router = APIRouter(prefix="/tools/notes", tags=["Tools: Notes"])

def current_user_id() -> str:
    return "demo-user"

class NoteIn(BaseModel):
    text: str
    tags: list[str] | None = None

@router.post("")
def api_notes_create(inb: NoteIn):
    return create_note(current_user_id(), inb.text, inb.tags or [])

class NotesSumIn(BaseModel):
    tag: str | None = None
    since: str | None = None

@router.post("/summarize")
def api_notes_summarize(inb: NotesSumIn):
    return summarize_notes(current_user_id(), tag=inb.tag, since=inb.since)
