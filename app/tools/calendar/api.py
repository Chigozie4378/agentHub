# app/tools/calendar/api.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.shared.http import ok, err
from app.shared.guard import guard_gate, bump_after_tool
from .service import create_event, update_event, delete_event, list_events, mark_date

router = APIRouter(prefix="/tools/calendar", tags=["Tools: Calendar"])

def current_user_id() -> str: return "demo-user"

class EventCreateIn(BaseModel):
    title: str
    start: str
    end: str | None = None
    location: str | None = None

class EventUpdateIn(BaseModel):
    event_id: str
    title: str | None = None
    start: str | None = None
    end: str | None = None
    location: str | None = None

@router.post("/create_event")
def api_calendar_create(inb: EventCreateIn, ctx=Depends(guard_gate("calendar"))):
    item = create_event(current_user_id(), **inb.model_dump())
    bump_after_tool(ctx, token_cost=1500)
    return ok(item)

@router.post("/update_event")
def api_calendar_update(inb: EventUpdateIn, ctx=Depends(guard_gate("calendar"))):
    eid = inb.event_id
    payload = inb.model_dump(exclude={"event_id"})
    item = update_event(current_user_id(), eid, **payload)
    bump_after_tool(ctx, token_cost=1200)
    return ok(item)

@router.delete("/delete_event/{event_id}")
def api_calendar_delete(event_id: str, ctx=Depends(guard_gate("calendar"))):
    ok_ = delete_event(current_user_id(), event_id)
    bump_after_tool(ctx, token_cost=800)
    return ok({"deleted": ok_})

@router.get("/list_events")
def api_calendar_list(start: str | None = None, end: str | None = None, ctx=Depends(guard_gate("calendar"))):
    items = list_events(current_user_id(), start=start, end=end)
    bump_after_tool(ctx, token_cost=900)
    return ok({"items": items})

class MarkDateIn(BaseModel):
    date: str
    label: str

@router.post("/mark_date")
def api_calendar_mark(inb: MarkDateIn, ctx=Depends(guard_gate("calendar"))):
    out = mark_date(current_user_id(), date=inb.date, label=inb.label)
    bump_after_tool(ctx, token_cost=600)
    return ok(out)
