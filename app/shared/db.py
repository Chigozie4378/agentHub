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

from sqlalchemy import text

def run_sqlite_migrations():
    with engine.begin() as conn:
        conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS user_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            day TEXT NOT NULL,                 -- YYYYMMDD
            tasks INTEGER NOT NULL DEFAULT 0,
            tokens INTEGER NOT NULL DEFAULT 0
        );
        """)
        # add the runs columns if not present (from earlier step)
        cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(runs)").fetchall()]
        if "needs_confirmation" not in cols:
            conn.exec_driver_sql("ALTER TABLE runs ADD COLUMN needs_confirmation BOOLEAN DEFAULT 0")
        if "pending_payload_json" not in cols:
            conn.exec_driver_sql("ALTER TABLE runs ADD COLUMN pending_payload_json TEXT DEFAULT '{}'")

