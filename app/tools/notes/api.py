from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.shared.guard import guard_gate, bump_after_tool

router = APIRouter(prefix="/tools/notes", tags=["Tools: Notes"])

class NoteCreate(BaseModel):
    text: str
    tags: Optional[List[str]] = None

class NoteItem(BaseModel):
    id: str
    text: str
    tags: List[str] = []

_MEM: dict[str, NoteItem] = {}

@router.post("", summary="Create note")
def create_note(body: NoteCreate, ctx=Depends(guard_gate("notes"))):
    import uuid
    nid = uuid.uuid4().hex
    item = NoteItem(id=nid, text=body.text, tags=body.tags or [])
    _MEM[nid] = item
    bump_after_tool(ctx, token_cost=400)
    return {"ok": True, "id": nid, "item": item.model_dump()}

class NotesSummReq(BaseModel):
    tag: Optional[str] = None
    since: Optional[str] = None  # ISO date

@router.post("/summarize", summary="Summarize notes (baseline concat; later LLM)")
def summarize_notes(req: NotesSummReq, ctx=Depends(guard_gate("notes"))):
    items = list(_MEM.values())
    if req.tag:
        items = [i for i in items if req.tag in i.tags]
    text = "\n\n".join(i.text for i in items)
    # TODO: swap with LLM later
    summary = text[:800] + ("..." if len(text) > 800 else "")
    bump_after_tool(ctx, token_cost=1200)
    return {"ok": True, "summary": summary, "count": len(items)}
