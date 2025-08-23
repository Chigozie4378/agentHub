from sqlalchemy.orm import Session
from app.files.models import File
from app.files.storage import save_upload, sniff_mime
from fastapi import UploadFile

# Text Extraction Service
from typing import List, Dict, Any, Tuple
from app.files.parse_inline import (
    extract_pdf_text, extract_docx_text, extract_csv_or_xlsx, extract_text_file, extract_image_meta
)


async def create_file_record(db: Session, user_id: str, uploaded: UploadFile) -> File:
    path, size, digest = await save_upload(uploaded)
    mime = sniff_mime(uploaded.filename or "", uploaded.content_type)
    rec = File(
        user_id=user_id,
        filename=uploaded.filename or "upload.bin",
        mime=mime,
        size=size,
        sha256=digest,
        storage_path=str(path),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def get_file(db: Session, user_id: str, file_id: str) -> File | None:
    f = db.get(File, file_id)
    if not f or f.user_id != user_id:
        return None
    return f




def get_file_many(db: Session, user_id: str, ids: List[str]) -> List[File]:
    out = []
    for fid in ids or []:
        f = db.get(File, fid)
        if f and f.user_id == user_id:
            out.append(f)
    return out

def inline_bundle_for_files(files: List[File]) -> dict:
    sources: List[Dict[str, Any]] = []
    texts: List[str] = []
    for f in files:
        t, meta = _extract_for(f)
        src = {"file_id": f.id, "filename": f.filename, "mime": f.mime, "meta": meta}
        sources.append(src)
        if t:
            texts.append(f"\n\n==== {f.filename} ====\n{t}")
        # special note for likely scanned PDFs
        if (not t.strip()) and (f.filename.lower().endswith(".pdf")):
            src.setdefault("meta", {})["note"] = "pdf_may_be_scanned_no_text"
    return {"sources": sources, "text": "".join(texts)[:80_000]}

def _extract_for(f: File) -> Tuple[str, dict]:
    mime = (f.mime or "").lower()
    path = f.storage_path
    name = f.filename.lower()

    if mime.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return extract_image_meta(path)
    if mime.startswith("application/pdf") or name.endswith(".pdf"):
        return extract_pdf_text(path)
    if mime.endswith("officedocument.wordprocessingml.document") or name.endswith(".docx"):
        return extract_docx_text(path)
    if name.endswith((".csv", ".xlsx", ".xls")):
        return extract_csv_or_xlsx(path)
    if mime.startswith("text/") or name.endswith((".txt", ".md")):
        return extract_text_file(path)
    return ("", {"note": "unsupported"})