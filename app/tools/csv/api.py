# app/tools/csv/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.shared.db import get_db
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import preview_csv

router = APIRouter(prefix="/tools/csv", tags=["Tools: CSV"])

def current_user_id() -> str:
    # TODO: replace with real auth/JWT extraction
    return "demo-user"

class CSVPreviewIn(BaseModel):
    file_id: str = Field(..., examples=["f_123"])
    limit: int | None = Field(50, ge=1, le=5000)

@router.post("/preview", summary="Preview a CSV (headers + first N rows) and store a normalized copy")
def api_csv_preview(
    inb: CSVPreviewIn,
    ctx = Depends(guard_gate("csv")),
    db: Session = Depends(get_db),
):
    try:
        out = preview_csv(db, current_user_id(), inb.file_id, limit=inb.limit or 50)
        if not out.get("ok"):
            return err("csv_failed", status=500, details=out.get("error") or "Unknown error")
        bump_after_tool(ctx, token_cost=1500)
        return ok(out)
    except FileNotFoundError as e:
        return err("file_not_found", status=404, details=str(e))
    except ValueError as e:
        return err("invalid_input", status=400, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
