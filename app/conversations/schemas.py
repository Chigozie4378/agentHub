# add this import
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default="New chat", max_length=200)

class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    archived: Optional[bool] = None

class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    archived: bool
    # ↓ Use datetime, not str
    created_at: datetime
    updated_at: datetime | None = None

class ConversationList(BaseModel):
    items: List[ConversationOut]
    next_cursor: str | None = None

# --- messages ---
class MessageCreate(BaseModel):
    text: str = Field(min_length=1)
    attachments: List[str] = Field(default_factory=list, description="Array of file IDs")
    context_mode: str = Field(default="inline", pattern="^(inline|ingest|none)$")
    context_scope: str = Field(default="message", pattern="^(message|conversation)$")

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conversation_id: str
    role: str
    text: str
    attachments: List[str]
    # ↓ Use datetime here too
    created_at: datetime

class MessageList(BaseModel):
    items: List[MessageOut]
    next_cursor: str | None = None
