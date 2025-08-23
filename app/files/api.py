from fastapi import APIRouter, UploadFile, File as Upload, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.shared.db import get_db
from app.files.schemas import FileOut, SignedUrlOut
from app.files.service import create_file_record, get_file

router = APIRouter(prefix="/files", tags=["Files"])

def current_user_id() -> str:
    return "demo-user"

@router.post("", response_model=FileOut, status_code=201)
async def upload_file(file: UploadFile = Upload(...), db: Session = Depends(get_db)):
    try:
        rec = await create_file_record(db, current_user_id(), file)
        return rec
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/{file_id}", response_model=FileOut)
def file_meta(file_id: str, db: Session = Depends(get_db)):
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    return f

@router.get("/{file_id}/download", response_model=SignedUrlOut)
def file_download(file_id: str, db: Session = Depends(get_db)):
    """
    Dev-friendly download: we serve the file via a one-off URL /files/raw/{id}.
    In prod you'd return an S3 pre-signed URL instead.
    """
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    # issue a short-lived URL under /files/raw/{id}
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    return {"url": f"/files/raw/{file_id}", "expires_at": expires}

# raw file responder (simple, dev-only)
@router.get("/raw/{file_id}")
def raw_file(file_id: str, db: Session = Depends(get_db)):
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    return FileResponse(
        path=f.storage_path,
        media_type=f.mime,
        filename=f.filename,
    )
