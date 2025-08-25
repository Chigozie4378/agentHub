# app/tools/summarize/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from app.shared.db import get_db
from app.files.service import get_file  # expects (db, user_id, file_id)
from .service import summarize_document

router = APIRouter(prefix="/tools/summarize", tags=["Tools: Summarize"])

def current_user_id() -> str:
    return "demo-user"

class SummarizeIn(BaseModel):
    file_id: str
    max_chars: int | None = 800

@router.post("/document")
def api_summarize_document(inb: SummarizeIn, ctx=Depends(guard_gate("summarize")), db: Session = Depends(get_db)):
    try:
        uid = current_user_id()
        out = summarize_document(db, uid, inb.file_id, max_chars=inb.max_chars or 800)
        bump_after_tool(ctx, token_cost=3500)
        return ok(out)
    except FileNotFoundError as e:
        return err("file_not_found", status=404, details=str(e))
    except ValueError as e:
        return err("invalid_input", status=400, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
