from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.db import Base
import uuid, json

def _id32() -> str:
    return uuid.uuid4().hex  # 32 chars

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id32)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200), default="New chat")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id32)
    conversation_id: Mapped[str] = mapped_column(String(32), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16), default="user")  # user|assistant|system
    text: Mapped[str] = mapped_column(Text, default="")
    # store attachments as JSON text for SQLite; service will dump/load list[str]
    attachments_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @property
    def attachments(self) -> list[str]:
        try:
            return json.loads(self.attachments_json or "[]")
        except Exception:
            return []

    @attachments.setter
    def attachments(self, val: list[str]):
        self.attachments_json = json.dumps(val or [])
