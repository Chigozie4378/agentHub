from fastapi import APIRouter
from pydantic import BaseModel
from .service import preview_csv

router = APIRouter(prefix="/tools/csv", tags=["Tools: CSV"])

class CsvPreviewIn(BaseModel):
    file_id: str
    limit: int | None = 50

@router.post("/preview")
def api_csv_preview(inb: CsvPreviewIn):
    return preview_csv(file_id=inb.file_id, limit=inb.limit or 50)
