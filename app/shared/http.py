from fastapi import HTTPException
from typing import Any, Optional

def ok(data: Any = None, **extra):
    return {"ok": True, "data": data, **extra}

def err(message: str, code: str = "bad_request", status: int = 400, details: Optional[Any] = None):
    # raise OR return; pick one style. I prefer raising to short-circuit.
    raise HTTPException(status_code=status, detail={"ok": False, "error": {"code": code, "message": message, "details": details}})
