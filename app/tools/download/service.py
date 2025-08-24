# app/tools/download/service.py
from pathlib import Path
import uuid, urllib.request

ARTIFACTS = Path("storage/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def fetch(url: str):
    if not url:
        raise ValueError("url required")
    out = ARTIFACTS / f"download_{uuid.uuid4().hex}"
    # naive filename guess
    if "." in url.rsplit("/", 1)[-1]:
        out = out.with_suffix("." + url.rsplit(".", 1)[-1])

    urllib.request.urlretrieve(url, out)
    size = out.stat().st_size
    return {"ok": True, "artifact_path": str(out), "size": size}
