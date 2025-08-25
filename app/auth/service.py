import uuid, bcrypt
from sqlalchemy.orm import Session
from app.auth.models import User

def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def _verify(pw: str, ph: str) -> bool:
    try: return bcrypt.checkpw(pw.encode(), ph.encode())
    except Exception: return False

def register_user(db: Session, email: str, password: str) -> dict:
    email = email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise ValueError("email_already_registered")
    u = User(id=str(uuid.uuid4()), email=email, password_hash=_hash(password))
    db.add(u); db.commit(); db.refresh(u)
    return {"id": u.id, "email": u.email, "tier": u.tier, "role": u.role}

def authenticate_user(db: Session, email: str, password: str) -> dict | None:
    u = db.query(User).filter(User.email == email.lower().strip()).first()
    if not u or not _verify(password, u.password_hash):
        return None
    return {"sub": u.id, "email": u.email, "tier": u.tier, "role": u.role}
