from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl
from .service import fetch

router = APIRouter(prefix="/tools/download", tags=["Tools: Download"])

class DownloadIn(BaseModel):
    url: HttpUrl

@router.post("/fetch")
def api_download(inb: DownloadIn):
    return fetch(str(inb.url))
