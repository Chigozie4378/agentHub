from fastapi import APIRouter, Depends
from pydantic import BaseModel, AnyUrl
from typing import List, Dict, Any, Optional
from app.shared.guard import guard_gate, bump_after_tool
from .service import browse


router = APIRouter(prefix="/tools/browser", tags=["Tools: Browser"])

class Action(BaseModel):
    type: str                      # "goto" | "click" | "type" | "scroll" | "wait_for" | "wait"
    url: Optional[str] = None      # for goto
    selector: Optional[str] = None # for click/type/wait_for
    text: Optional[str] = None     # for type
    y: Optional[int] = None        # for scroll
    ms: Optional[int] = None       # for wait (sleep milliseconds)

class BrowseReq(BaseModel):
    url: AnyUrl
    actions: Optional[List[Action]] = None

@router.post("", summary="Open a page, perform actions, and take a screenshot")
async def api_browse(body: BrowseReq, ctx = Depends(guard_gate("browser"))):
    out = await browse(str(body.url), [a.model_dump() for a in (body.actions or [])])
    if out.get("ok"):
        bump_after_tool(ctx, token_cost=8000)
    return out