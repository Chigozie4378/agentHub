from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from urllib.parse import quote_plus
from app.shared.guard import guard_gate, bump_after_tool

router = APIRouter(prefix="/tools/places", tags=["Tools: Places"])

class PlacesReq(BaseModel):
    q: str
    near: Optional[str] = None

@router.post("/search", summary="Dry-run: build query URLs for restaurant/business search")
def api_places_search(req: PlacesReq, ctx = Depends(guard_gate("places"))):
    q = req.q + (f" near {req.near}" if req.near else "")
    urls: List[str] = [
        f"https://www.google.com/maps/search/{quote_plus(q)}",
        f"https://www.yelp.com/search?find_desc={quote_plus(req.q)}&find_loc={quote_plus(req.near or '')}",
        f"https://duckduckgo.com/?q={quote_plus(req.q)}"
    ]
    bump_after_tool(ctx, token_cost=1200)
    return {"ok": True, "query": q, "links": urls}
