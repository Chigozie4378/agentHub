from fastapi import APIRouter
from pydantic import BaseModel
from .service import search_places

router = APIRouter(prefix="/tools/places", tags=["Tools: Places"])

class PlacesIn(BaseModel):
    q: str
    near: str | None = None

@router.post("/search")
def api_places_search(inb: PlacesIn):
    return search_places(q=inb.q, near=inb.near)
