# app/tools/notes/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import create_note, summarize_notes

router = APIRouter(prefix="/tools/notes", tags=["Tools: Notes"])

def current_user_id() -> str: return "demo-user"

class NoteCreateIn(BaseModel):
    text: str
    tags: list[str] | None = None

class NotesSummarizeIn(BaseModel):
    tag: str | None = None
    since: str | None = None

@router.post("/create")
def api_notes_create(inb: NoteCreateIn, ctx=Depends(guard_gate("notes"))):
    item = create_note(current_user_id(), inb.text, inb.tags or [])
    bump_after_tool(ctx, token_cost=700)
    return ok(item)

@router.post("/summarize")
def api_notes_summarize(inb: NotesSummarizeIn, ctx=Depends(guard_gate("notes"))):
    out = summarize_notes(current_user_id(), tag=inb.tag, since=inb.since)
    bump_after_tool(ctx, token_cost=2500)
    return ok(out)
