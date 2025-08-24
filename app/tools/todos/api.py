from fastapi import APIRouter, Path, Query
from pydantic import BaseModel
from typing import Literal
from .service import create_todo, list_todos, update_todo, delete_todo

router = APIRouter(prefix="/tools/todos", tags=["Tools: Todos"])

def current_user_id() -> str:
    return "demo-user"

class TodoCreateIn(BaseModel):
    title: str
    due_at: str | None = None
    labels: list[str] | None = None

@router.post("")
def api_todo_create(inb: TodoCreateIn):
    return create_todo(current_user_id(), inb.title, inb.due_at, inb.labels or [])

@router.get("")
def api_todo_list(status: Literal["pending","completed"] | None = Query(default=None)):
    return list_todos(current_user_id(), status=status)

class TodoUpdateIn(BaseModel):
    status: Literal["pending","completed"] | None = None

@router.patch("/{todo_id}")
def api_todo_update(todo_id: str = Path(...), inb: TodoUpdateIn | None = None):
    data = inb.dict(exclude_unset=True) if inb else {}
    return update_todo(current_user_id(), todo_id, status=data.get("status"))

@router.delete("/{todo_id}")
def api_todo_delete(todo_id: str = Path(...)):
    return {"ok": delete_todo(current_user_id(), todo_id)}
