from jsonschema import Draft202012Validator, ValidationError
from typing import Any, Tuple
from .registry import REGISTRY

def validate_payload(schema: dict | None, payload: Any) -> Tuple[bool, str | None]:
    if not schema:
        return True, None
    try:
        Draft202012Validator(schema).validate(payload)
        return True, None
    except ValidationError as e:
        path = ".".join(str(p) for p in e.path)
        msg = f"{path or 'payload'}: {e.message}"
        return False, msg
def require_valid(tool_name: str, payload: dict):
    from fastapi import HTTPException
    meta = next((t for t in REGISTRY if t.get("name") == tool_name), None)
    if not meta:
        raise HTTPException(404, f"Unknown tool: {tool_name}")
    ok, err = validate_payload(meta.get("input_schema"), payload)
    if not ok:
        raise HTTPException(400, f"Invalid payload for {tool_name}: {err}")
    return meta
