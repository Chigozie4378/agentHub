from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Any

from .registry import REGISTRY
from .schema_validator import validate_payload

router = APIRouter(prefix="/tools", tags=["Tools"])

# Keep your existing endpoint
@router.get("/registry", summary="List all registered tools")
def list_tools():
    return {"items": REGISTRY, "count": len(REGISTRY)}

# New: search by keyword (name/summary)
@router.get("/registry/search", summary="Search tools by name/summary")
def search_tools(q: str = Query("", description="Keyword")):
    ql = q.lower().strip()
    items = [
        t for t in REGISTRY
        if not ql
        or ql in t.get("name", "").lower()
        or ql in t.get("summary", "").lower()
    ]
    items = sorted(items, key=lambda t: t.get("name", ""))[:50]
    return {"ok": True, "count": len(items), "items": items}

# New: validate a payload against a tool's input_schema
class ValidateReq(BaseModel):
    name: str
    payload: Any

@router.post("/registry/validate", summary="Validate payload against tool input_schema")
def validate_tool_payload(body: ValidateReq):
    meta = next((t for t in REGISTRY if t.get("name") == body.name), None)
    if not meta:
        raise HTTPException(404, f"Unknown tool: {body.name}")
    ok, err = validate_payload(meta.get("input_schema"), body.payload)
    return {"ok": ok, "error": err}
