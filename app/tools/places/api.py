# app/tools/places/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import search_places

router = APIRouter(prefix="/tools/places", tags=["Tools: Places"])

class PlacesIn(BaseModel):
    q: str
    near: str | None = None

@router.post("/search")
def api_places(inb: PlacesIn, ctx=Depends(guard_gate("places"))):
    try:
        out = search_places(q=inb.q, near=inb.near)
        bump_after_tool(ctx, token_cost=2000)
        return ok(out)
    except ValueError as e:
        return err("invalid_query", code="invalid_query", status=400, details=str(e))
    except Exception as e:
        return err("tool_failed", status=500, details=str(e))
