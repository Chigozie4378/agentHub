# app/tools/browser/api.py
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, AnyUrl

from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
# If you want idempotency/caching, uncomment these:
# from sqlalchemy.orm import Session
# from app.shared.db import get_db
# from app.shared.idempotency import require_idem, save_idem

from .service import browse  # async def browse(url: str, actions: list[dict] | None) -> dict

router = APIRouter(prefix="/tools/browser", tags=["Tools: Browser"])

ActionType = Literal["goto", "click", "type", "scroll", "wait_for", "wait"]

class Action(BaseModel):
    type: ActionType
    url: Optional[str] = None        # for goto
    selector: Optional[str] = None   # for click/type/wait_for
    text: Optional[str] = None       # for type
    y: Optional[int] = None          # for scroll
    ms: Optional[int] = None         # for wait (sleep milliseconds)

class BrowseReq(BaseModel):
    url: AnyUrl
    actions: Optional[List[Action]] = None

@router.post("", summary="Open a page, perform actions, and take a screenshot")
async def api_browse(
    body: BrowseReq,
    ctx = Depends(guard_gate("browser")),
    # If you enable idempotency, also add:
    # db: Session = Depends(get_db),
    # idem = Depends(lambda db=db, body=body: require_idem(db=db, payload=body.model_dump())),
):
    try:
        out = await browse(str(body.url), [a.model_dump() for a in (body.actions or [])])

        # Expect your service to return {"ok": True, "screenshot_path": "...", ...}
        if not out.get("ok"):
            return err(
                "browser_failed",
                status=500,
                details=out.get("error") or "Unknown browser error"
            )

        bump_after_tool(ctx, token_cost=8000)

        # If you enable idempotency:
        # resp = ok(out)
        # save_idem(db, idem.get("idem"), resp)
        # return resp

        return ok(out)

    except ValueError as e:
        # e.g., bad selector, invalid action
        return err("invalid_input", status=400, details=str(e))
    except Exception as e:
        # Playwright/OS errors, timeouts, etc.
        return err("tool_failed", status=500, details=str(e))
