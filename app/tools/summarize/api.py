from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.shared.db import get_db
from .service import summarize_document

router = APIRouter(prefix="/tools/summarize", tags=["Tools: Summarize"])

def current_user_id() -> str:
    return "demo-user"

class SummDocIn(BaseModel):
    file_id: str
    max_chars: int | None = 800

@router.post("/document")
def api_summarize_document(inb: SummDocIn, db: Session = Depends(get_db)):
    out = summarize_document(db, current_user_id(), inb.file_id, max_chars=inb.max_chars or 800)
    if out.get("error") == "file_not_found":
        raise HTTPException(status_code=404, detail=f"File not found: {inb.file_id}")
    return out
