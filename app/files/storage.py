from pathlib import Path
from hashlib import sha256
from typing import Tuple
import mimetypes
from fastapi import UploadFile

# Resolve a safe, writable storage path
ROOT = Path(__file__).resolve().parents[2]   # project root
UPLOADS_DIR = ROOT / "storage" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Limits
MAX_BYTES = 25 * 1024 * 1024  # 25 MB per file
MAX_FILES_PER_REQUEST = 5

# Allowlist (extensions + loose MIME checks)
ALLOWED_EXTS = {
    ".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx", ".xls",
    ".png", ".jpg", ".jpeg", ".webp"
}
ALLOWED_MIME_PREFIXES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/",
    "image/",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/csv",
}

def _safe_name(name: str) -> str:
    return Path(name).name.replace("..", "_")

def sniff_mime(filename: str, fallback: str | None) -> str:
    guess, _ = mimetypes.guess_type(filename)
    return fallback or guess or "application/octet-stream"

def is_allowed(filename: str, content_type: str | None) -> bool:
    ext_ok = Path(filename).suffix.lower() in ALLOWED_EXTS
    mime = (content_type or "").lower()
    mime_ok = any(mime.startswith(p) for p in ALLOWED_MIME_PREFIXES)
    # be permissive if ext is allowed even if browser misreports MIME
    return ext_ok or mime_ok

async def save_upload(file: UploadFile) -> Tuple[Path, int, str]:
    """
    Save to disk under storage/uploads and return (path, size, sha256hex).
    Raises ValueError with user-friendly messages on validation errors.
    """
    fname = _safe_name(file.filename or "upload.bin")
    if not is_allowed(fname, file.content_type):
        raise ValueError("Unsupported file type. Allowed: pdf, docx, txt/md, csv/xlsx, png/jpg/webp")

    target = UPLOADS_DIR / fname
    h = sha256()
    size = 0

    with target.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_BYTES:
                out.close()
                target.unlink(missing_ok=True)
                raise ValueError("File too large. Max 25 MB")
            h.update(chunk)
            out.write(chunk)

    await file.close()
    return target, size, h.hexdigest()
