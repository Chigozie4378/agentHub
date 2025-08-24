from fastapi import APIRouter

from .registry import REGISTRY

router = APIRouter(prefix="/tools", tags=["Tools"])

@router.get("/registry")
def list_tools():
    return {"items": REGISTRY, "count": len(REGISTRY)}
