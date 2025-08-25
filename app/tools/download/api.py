# app/tools/download/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from app.shared.db import get_db
from app.shared.idem import require_idem, save_idem
from .service import fetch

router = APIRouter(prefix="/tools/download", tags=["Tools: Download"])

class DownloadIn(BaseModel):
    url: HttpUrl

@router.post("/fetch")
def api_download(
    inb: DownloadIn,
    ctx=Depends(guard_gate("download")),
    db: Session = Depends(get_db),
    idem=Depends(lambda db=Depends(get_db), inb=Depends(DownloadIn): require_idem(db=db, payload=inb.model_dump())),
):
    try:
        out = fetch(str(inb.url))
        resp = ok(out)
        save_idem(db, idem.get("idem"), resp)
        bump_after_tool(ctx, token_cost=2000)
        return resp
    except ValueError as e:
        return err("invalid_download", code="invalid_download", status=400, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
