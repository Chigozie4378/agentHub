from fastapi import APIRouter, Depends
from pydantic import BaseModel, AnyUrl
import httpx
from app.shared.guard import guard_gate, bump_after_tool
from app.shared.artifacts import save_bytes
from pathlib import Path

router = APIRouter(prefix="/tools/download", tags=["Tools: Download"])

class DownloadReq(BaseModel):
    url: AnyUrl

@router.post("", summary="Download a file and store as artifact")
def download_file(req: DownloadReq, ctx=Depends(guard_gate("download"))):
    try:
        with httpx.stream("GET", str(req.url), timeout=30) as r:
            r.raise_for_status()
            content = r.read()
    except Exception as e:
        return {"ok": False, "error": "download_failed", "detail": repr(e)}

    # naive filename guess
    name = Path(str(req.url)).name or "file"
    # strip query junk
    if "?" in name: name = name.split("?",1)[0]
    # pick extension if any
    if "." in name:
        stem, ext = name.rsplit(".",1)
        path = save_bytes(stem, ext, content)
    else:
        path = save_bytes("download", "bin", content)

    bump_after_tool(ctx, token_cost=1500)
    return {"ok": True, "artifact_path": path, "size": len(content)}
