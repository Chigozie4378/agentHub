# app/tools/csv/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import preview_csv

router = APIRouter(prefix="/tools/csv", tags=["Tools: CSV"])

class CSVPreviewIn(BaseModel):
    file_id: str
    limit: int | None = 50

@router.post("/preview")
def api_csv_preview(inb: CSVPreviewIn, ctx=Depends(guard_gate("csv"))):
    try:
        out = preview_csv(file_id=inb.file_id, limit=inb.limit or 50)
        bump_after_tool(ctx, token_cost=1500)
        return ok(out)
    except FileNotFoundError as e:
        return err("file_not_found", status=404, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
