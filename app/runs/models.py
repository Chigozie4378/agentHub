from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.db import Base
import uuid, json

def _id32() -> str:
    return uuid.uuid4().hex

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id32)
    conversation_id: Mapped[str] = mapped_column(String(32), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="running")  # queued|running|completed|failed|cancelled
    mode: Mapped[str] = mapped_column(String(16), default="chat")       # chat|qa_rag|task
    plan_json: Mapped[str] = mapped_column(Text, default="[]")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def plan(self) -> list[str]:
        try:
            return json.loads(self.plan_json or "[]")
        except Exception:
            return []

    @plan.setter
    def plan(self, val: list[str]):
        self.plan_json = json.dumps(val or [])

class Step(Base):
    __tablename__ = "steps"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id32)
    run_id: Mapped[str] = mapped_column(String(32), ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    idx: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str] = mapped_column(String(32), default="info")  # plan|tool|token|final
    data_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(16), default="completed")  # started|completed|failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @property
    def data(self) -> dict:
        try:
            return json.loads(self.data_json or "{}")
        except Exception:
            return {}

    @data.setter
    def data(self, val: dict):
        self.data_json = json.dumps(val or {})
