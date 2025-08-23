from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Local SQLite DB under ./storage/ (created if missing)
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]   # project root
STORAGE_DIR = ROOT / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DB_URL = f"sqlite:///{(STORAGE_DIR / 'agenthub.db').as_posix()}"


engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

# FastAPI dep
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
