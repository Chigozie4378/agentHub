# app/tools/browser/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any
from app.shared.db import get_db
from .service import browse

# robust way to get the installed version
from importlib.metadata import version, PackageNotFoundError
try:
    pw_version = version("playwright")
except PackageNotFoundError:
    pw_version = "unknown"

router = APIRouter(prefix="/tools/browser", tags=["Tools: Browser"])

class BrowseReq(BaseModel):
    url: HttpUrl
    actions: List[Dict[str, Any]] = Field(default_factory=list)

@router.post("", summary="Open a page and take a screenshot")
async def api_browse(body: BrowseReq, db = Depends(get_db)):
    out = await browse(str(body.url), body.actions)
    out.setdefault("playwright_version", pw_version)
    return out

@router.get("/diagnose", summary="Check Playwright availability")
def diagnose():
    return {"ok": True, "playwright_version": pw_version}
