from sqlalchemy.orm import Session
from app.files.models import File
from app.files.storage import save_upload, sniff_mime
from fastapi import UploadFile

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
