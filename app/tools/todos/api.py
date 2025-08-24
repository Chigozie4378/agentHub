from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.shared.guard import guard_gate, bump_after_tool

router = APIRouter(prefix="/tools/todos", tags=["Tools: Todos"])

class TodoCreate(BaseModel):
    title: str
    due_at: Optional[str] = None  # ISO8601
    labels: Optional[List[str]] = None

class TodoItem(BaseModel):
    id: str
    title: str
    status: str = "pending"  # pending|completed
    due_at: Optional[str] = None
    labels: List[str] = []

# In-memory scratchpad for now (replace with DB later)
_MEM: dict[str, TodoItem] = {}

@router.post("", summary="Create todo item")
def create_todo(body: TodoCreate, ctx=Depends(guard_gate("todos"))):
    import uuid
    tid = uuid.uuid4().hex
    item = TodoItem(id=tid, title=body.title, due_at=body.due_at, labels=body.labels or [])
    _MEM[tid] = item
    bump_after_tool(ctx, token_cost=500)
    return {"ok": True, "id": tid, "item": item.model_dump()}

@router.get("", summary="List todo items")
def list_todos(status: Optional[str] = Query(None, pattern="^(pending|completed)$"), ctx=Depends(guard_gate("todos"))):
    items = list(_MEM.values())
    if status:
        items = [i for i in items if i.status == status]
    return {"ok": True, "items": [i.model_dump() for i in items]}

@router.patch("/{todo_id}", summary="Mark complete or update")
def update_todo(todo_id: str, status: Optional[str] = Query(None, pattern="^(pending|completed)$"), ctx=Depends(guard_gate("todos"))):
    if todo_id not in _MEM: raise HTTPException(404, "Not found")
    if status: _MEM[todo_id].status = status
    bump_after_tool(ctx, token_cost=300)
    return {"ok": True, "item": _MEM[todo_id].model_dump()}

@router.delete("/{todo_id}", summary="Delete todo item")
def delete_todo(todo_id: str, ctx=Depends(guard_gate("todos"))):
    _MEM.pop(todo_id, None)
    return {"ok": True}
