from pathlib import Path
from hashlib import sha256
from typing import Tuple
import os, mimetypes
from fastapi import UploadFile

# Resolve a safe, writable storage path
ROOT = Path(__file__).resolve().parents[2]   # project root (…/agenthub)
UPLOADS_DIR = ROOT / "storage" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 25 * 1024 * 1024  # 25 MB

def _safe_name(name: str) -> str:
    # strip directories & weird chars
    return Path(name).name.replace("..", "_")

def sniff_mime(filename: str, fallback: str | None) -> str:
    guess, _ = mimetypes.guess_type(filename)
    return fallback or guess or "application/octet-stream"

async def save_upload(file: UploadFile) -> Tuple[Path, int, str]:
    """
    Save to disk under storage/uploads and return (path, size, sha256hex).
    """
    fname = _safe_name(file.filename or "upload.bin")
    target = UPLOADS_DIR / fname

    h = sha256()
    size = 0
    # write in chunks
    with target.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_BYTES:
                out.close()
                target.unlink(missing_ok=True)
                raise ValueError("File too large")
            h.update(chunk)
            out.write(chunk)

    await file.close()
    return target, size, h.hexdigest()
