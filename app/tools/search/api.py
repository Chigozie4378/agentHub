# app/tools/search/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from app.shared.db import get_db
from .service import web_search

router = APIRouter(prefix="/tools/search", tags=["Tools: Search"])

class WebSearchIn(BaseModel):
    q: str

@router.post("/web")
def api_search_web(inb: WebSearchIn, ctx=Depends(guard_gate("search")), db: Session = Depends(get_db)):
    try:
        links = web_search(inb.q)
        bump_after_tool(ctx, token_cost=2500)
        return ok({"links": links})
    except ValueError as e:
        return err("invalid_query", code="invalid_query", status=400, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
