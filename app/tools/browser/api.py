from fastapi import APIRouter, Depends
from pydantic import BaseModel, AnyUrl
from typing import List, Dict, Any, Optional
from app.shared.guard import guard_gate, bump_after_tool
from .service import browse


router = APIRouter(prefix="/tools/browser", tags=["Tools: Browser"])

class Action(BaseModel):
    type: str
    selector: Optional[str] = None
    text: Optional[str] = None
    y: Optional[int] = None
    url: Optional[str] = None

class BrowseReq(BaseModel):
    url: AnyUrl
    actions: Optional[List[Action]] = None

@router.post("", summary="Open a page and take a screenshot")
async def api_browse(body: BrowseReq, ctx = Depends(guard_gate("browser"))):
    out = await browse(str(body.url), [a.model_dump() for a in body.actions] if body.actions else None)
    # Always return JSON; bump usage only on success
    if out.get("ok"):
        bump_after_tool(ctx, token_cost=8000)
    return out
