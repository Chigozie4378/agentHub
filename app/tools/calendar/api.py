from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.shared.guard import guard_gate, bump_after_tool

router = APIRouter(prefix="/tools/calendar", tags=["Tools: Calendar"])

class EventCreate(BaseModel):
    title: str
    start: str  # ISO8601
    end: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[EmailStr]] = None

class EventItem(BaseModel):
    id: str
    title: str
    start: str
    end: Optional[str] = None
    location: Optional[str] = None
    attendees: List[str] = []
    status: str = "confirmed"

_MEM: dict[str, EventItem] = {}

@router.post("/events", summary="Create event")
def create_event(body: EventCreate, ctx=Depends(guard_gate("calendar"))):
    import uuid
    eid = uuid.uuid4().hex
    item = EventItem(id=eid, **body.model_dump(), attendees=[*body.attendees] if body.attendees else [])
    _MEM[eid] = item
    bump_after_tool(ctx, token_cost=900)
    return {"ok": True, "id": eid, "item": item.model_dump()}

@router.patch("/events/{event_id}", summary="Reschedule/update")
def reschedule_event(event_id: str, body: EventCreate, ctx=Depends(guard_gate("calendar"))):
    if event_id not in _MEM: raise HTTPException(404, "Not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(_MEM[event_id], k, v)
    return {"ok": True, "item": _MEM[event_id].model_dump()}

@router.delete("/events/{event_id}", summary="Delete event")
def delete_event(event_id: str, ctx=Depends(guard_gate("calendar"))):
    _MEM.pop(event_id, None)
    return {"ok": True}

@router.get("/events", summary="List events (time-range optional)")
def list_events(start: Optional[str] = Query(None), end: Optional[str] = Query(None), ctx=Depends(guard_gate("calendar"))):
    # TODO: filter by time window
    return {"ok": True, "items": [e.model_dump() for e in _MEM.values()]}

class MarkDateReq(BaseModel):
    date: str
    label: str

@router.post("/mark-date", summary="Flag a date")
def mark_date(req: MarkDateReq, ctx=Depends(guard_gate("calendar"))):
    bump_after_tool(ctx, token_cost=300)
    # TODO: persist “markers” table if needed
    return {"ok": True, "marked": req.model_dump()}
