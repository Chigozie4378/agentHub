# app/tools/todos/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import create_todo, list_todos, update_todo, delete_todo

router = APIRouter(prefix="/tools/todos", tags=["Tools: Todos"])

def current_user_id() -> str: return "demo-user"

class TodoCreateIn(BaseModel):
    title: str
    due_at: str | None = None
    labels: list[str] | None = None

class TodoUpdateIn(BaseModel):
    todo_id: str
    status: str | None = None
    title: str | None = None

@router.post("/create")
def api_todos_create(inb: TodoCreateIn, ctx=Depends(guard_gate("todos"))):
    try:
        item = create_todo(current_user_id(), inb.title, inb.due_at, inb.labels or [])
        bump_after_tool(ctx, token_cost=800)
        return ok(item)
    except ValueError as e:
        return err("invalid_input", status=400, details=str(e))

@router.get("/list")
def api_todos_list(status: str | None = None, ctx=Depends(guard_gate("todos"))):
    items = list_todos(current_user_id(), status=status)
    bump_after_tool(ctx, token_cost=600)
    return ok({"items": items})

@router.post("/update")
def api_todos_update(inb: TodoUpdateIn, ctx=Depends(guard_gate("todos"))):
    try:
        item = update_todo(current_user_id(), inb.todo_id, status=inb.status, title=inb.title)
        bump_after_tool(ctx, token_cost=700)
        return ok(item)
    except KeyError:
        return err("not_found", status=404)
    except ValueError as e:
        return err("invalid_input", status=400, details=str(e))

@router.delete("/delete/{todo_id}")
def api_todos_delete(todo_id: str, ctx=Depends(guard_gate("todos"))):
    ok_ = delete_todo(current_user_id(), todo_id)
    bump_after_tool(ctx, token_cost=500)
    return ok({"deleted": ok_})
