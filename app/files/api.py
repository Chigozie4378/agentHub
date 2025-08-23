from fastapi import APIRouter, UploadFile, File as Upload, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List

from app.shared.db import get_db
from app.files.schemas import FileOut, SignedUrlOut
from app.files.service import create_file_record, get_file
from app.files.storage import MAX_FILES_PER_REQUEST

router = APIRouter(prefix="/files", tags=["Files"])

def current_user_id() -> str:
    return "demo-user"

@router.post("", response_model=FileOut, status_code=201,
             summary="Upload a single file",
             description="Allowed: pdf, docx, txt/md, csv/xlsx, png/jpg/webp. Max 25 MB.")
async def upload_file(file: UploadFile = Upload(...), db: Session = Depends(get_db)):
    try:
        rec = await create_file_record(db, current_user_id(), file)
        return rec
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/batch", response_model=list[FileOut], status_code=201,
             summary="Upload multiple files (max 5)",
             description="Send up to 5 files as `files`. Same type/size limits as single upload.")
async def upload_files_batch(files: List[UploadFile] = Upload(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(400, "No files provided")
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(400, f"Too many files. Max {MAX_FILES_PER_REQUEST}")
    out: list[FileOut] = []
    for f in files:
        try:
            rec = await create_file_record(db, current_user_id(), f)
            out.append(rec)
        except ValueError as e:
            raise HTTPException(400, f"{f.filename}: {e}")
    return out

@router.get("/{file_id}", response_model=FileOut)
def file_meta(file_id: str, db: Session = Depends(get_db)):
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    return f

@router.get("/{file_id}/download", response_model=SignedUrlOut)
def file_download(file_id: str, db: Session = Depends(get_db)):
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    return {"url": f"/files/raw/{file_id}", "expires_at": expires}

@router.get("/raw/{file_id}")
def raw_file(file_id: str, db: Session = Depends(get_db)):
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    return FileResponse(path=f.storage_path, media_type=f.mime, filename=f.filename)
from fastapi import APIRouter, UploadFile, File as Upload, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List

from app.shared.db import get_db
from app.files.schemas import FileOut, SignedUrlOut
from app.files.service import create_file_record, get_file
from app.files.storage import MAX_FILES_PER_REQUEST

router = APIRouter(prefix="/files", tags=["Files"])

def current_user_id() -> str:
    return "demo-user"

@router.post("", response_model=FileOut, status_code=201,
             summary="Upload a single file",
             description="Allowed: pdf, docx, txt/md, csv/xlsx, png/jpg/webp. Max 25 MB.")
async def upload_file(file: UploadFile = Upload(...), db: Session = Depends(get_db)):
    try:
        rec = await create_file_record(db, current_user_id(), file)
        return rec
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/batch", response_model=list[FileOut], status_code=201,
             summary="Upload multiple files (max 5)",
             description="Send up to 5 files as `files`. Same type/size limits as single upload.")
async def upload_files_batch(files: List[UploadFile] = Upload(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(400, "No files provided")
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(400, f"Too many files. Max {MAX_FILES_PER_REQUEST}")
    out: list[FileOut] = []
    for f in files:
        try:
            rec = await create_file_record(db, current_user_id(), f)
            out.append(rec)
        except ValueError as e:
            raise HTTPException(400, f"{f.filename}: {e}")
    return out

@router.get("/{file_id}", response_model=FileOut)
def file_meta(file_id: str, db: Session = Depends(get_db)):
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    return f

@router.get("/{file_id}/download", response_model=SignedUrlOut)
def file_download(file_id: str, db: Session = Depends(get_db)):
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    return {"url": f"/files/raw/{file_id}", "expires_at": expires}

@router.get("/raw/{file_id}")
def raw_file(file_id: str, db: Session = Depends(get_db)):
    f = get_file(db, current_user_id(), file_id)
    if not f:
        raise HTTPException(404, "File not found")
    return FileResponse(path=f.storage_path, media_type=f.mime, filename=f.filename)
