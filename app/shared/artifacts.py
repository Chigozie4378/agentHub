from pathlib import Path
import uuid, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
ART_DIR = ROOT / "storage" / "artifacts"
ART_DIR.mkdir(parents=True, exist_ok=True)

def new_name(prefix: str, ext: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}.{ext.lstrip('.')}"

def save_bytes(prefix: str, ext: str, data: bytes) -> str:
    name = new_name(prefix, ext)
    path = ART_DIR / name
    path.write_bytes(data)
    return str(path)

def save_json(prefix: str, payload: dict) -> str:
    name = new_name(prefix, "json")
    path = ART_DIR / name
    payload = {"_saved_at": datetime.now(timezone.utc).isoformat(), **payload}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
