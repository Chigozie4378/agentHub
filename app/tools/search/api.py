from fastapi import APIRouter, Depends
from pydantic import BaseModel
from urllib.parse import quote_plus
from app.shared.guard import guard_gate, bump_after_tool

router = APIRouter(prefix="/tools/search", tags=["Tools: Search"])

class SearchReq(BaseModel):
    q: str

@router.post("/web", summary="Search the web (links only; add SerpAPI later)")
def search_web(req: SearchReq, ctx=Depends(guard_gate("search"))):
    q = quote_plus(req.q)
    links = [
        f"https://duckduckgo.com/?q={q}",
        f"https://www.google.com/search?q={q}",
        f"https://www.bing.com/search?q={q}"
    ]
    bump_after_tool(ctx, token_cost=600)
    return {"ok": True, "links": links}
