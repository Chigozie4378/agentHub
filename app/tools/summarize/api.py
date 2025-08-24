from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.shared.guard import guard_gate, bump_after_tool
from app.files.service import get_file
import re

router = APIRouter(prefix="/tools/summarize", tags=["Tools: Summarize"])

class SummReq(BaseModel):
    file_id: str
    max_chars: Optional[int] = 800

@router.post("", summary="Summarize a document (baseline heuristic)")
def summarize(req: SummReq, ctx=Depends(guard_gate("summarize"))):
    f = get_file(req.file_id)
    if not f: raise HTTPException(404, "File not found")
    # TODO: robust text extraction (pdfminer.six / python-docx etc.)
    raw = open(f["path"], "rb").read().decode(errors="ignore")
    # crude: collapse whitespace, keep first N chars
    text = re.sub(r"\s+", " ", raw).strip()
    summary = text[: (req.max_chars or 800)] + ("..." if len(text) > (req.max_chars or 800) else "")
    bump_after_tool(ctx, token_cost=2200)
    return {"ok": True, "summary": summary, "length": len(text)}
