from fastapi import APIRouter
from pydantic import BaseModel
from .service import web_search

router = APIRouter(prefix="/tools/search", tags=["Tools: Search"])

class WebSearchIn(BaseModel):
    q: str

@router.post("/web")
def api_web_search(inb: WebSearchIn):
    return web_search(q=inb.q)
