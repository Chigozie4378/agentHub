from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.conversations.models import Conversation, Message
from app.conversations.schemas import ConversationCreate, ConversationUpdate

def create_conversation(db: Session, user_id: str, payload: ConversationCreate) -> Conversation:
    conv = Conversation(user_id=user_id, title=payload.title or "New chat")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def get_conversation(db: Session, user_id: str, conv_id: str):
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user_id:
        return None
    return conv


def list_conversations(db: Session, user_id: str, limit: int = 20, cursor: str | None = None):
    stmt = select(Conversation).where(Conversation.user_id == user_id, Conversation.archived == False)
    if cursor:
        try:
            # cursor is ISO datetime string of created_at; return older items
            ts = datetime.fromisoformat(cursor)
            stmt = stmt.where(Conversation.created_at < ts)
        except Exception:
            pass
    stmt = stmt.order_by(desc(Conversation.created_at)).limit(min(limit, 100))
    rows = db.scalars(stmt).all()
    next_cursor = rows[-1].created_at.isoformat() if len(rows) == limit else None
    return rows, next_cursor

def update_conversation(db: Session, user_id: str, conv_id: str, payload: ConversationUpdate) -> Conversation | None:
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user_id:
        return None
    if payload.title is not None:
        conv.title = payload.title.strip() or conv.title
    if payload.archived is not None:
        conv.archived = bool(payload.archived)
    db.commit()
    db.refresh(conv)
    return conv

def soft_delete_conversation(db: Session, user_id: str, conv_id: str) -> bool:
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user_id:
        return False
    conv.archived = True
    db.commit()
    return True

def create_message(db: Session, user_id: str, conversation_id: str, text: str, attachments: list[str]) -> Message | None:
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.user_id != user_id or conv.archived:
        return None
    msg = Message(conversation_id=conversation_id, role="user", text=text)
    msg.attachments = attachments or []
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
