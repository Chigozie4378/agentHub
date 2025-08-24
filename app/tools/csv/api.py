from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import csv, io
from app.shared.guard import guard_gate, bump_after_tool
from app.files.service import get_file  # you already have file storage
from app.shared.artifacts import save_bytes

router = APIRouter(prefix="/tools/csv", tags=["Tools: CSV"])

class CsvPreviewReq(BaseModel):
    file_id: str
    limit: Optional[int] = 20

@router.post("/preview", summary="Preview CSV headers and first N rows")
def api_csv_preview(req: CsvPreviewReq, ctx = Depends(guard_gate("csv"))):
    f = get_file(req.file_id)
    if not f: raise HTTPException(404, "File not found")
    # assume 'path' exists in your file metadata
    raw = open(f["path"], "rb").read()
    text = raw.decode(errors="ignore")
    reader = csv.reader(io.StringIO(text))
    rows = []
    for i, r in enumerate(reader):
        rows.append(r)
        if i >= (req.limit or 20): break
    headers = rows[0] if rows else []
    # save normalized copy as artifact (optional)
    norm = "\n".join(",".join(r) for r in rows)
    norm_path = save_bytes("preview", "csv", norm.encode())
    bump_after_tool(ctx, token_cost=1500)
    return {"ok": True, "headers": headers, "rows": rows[1:], "normalized_csv_path": norm_path}
