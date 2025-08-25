# app/shared/config.py
from pydantic import BaseModel
import os

class Settings(BaseModel):
    ENV: str = os.getenv("ENV", "dev")
    DEFAULT_TIER: str = os.getenv("DEFAULT_TIER", "free")
    FREE_TASK_LIMIT: int = int(os.getenv("FREE_TASK_LIMIT", "50"))
    FREE_TOKEN_BUDGET: int = int(os.getenv("FREE_TOKEN_BUDGET", "200000"))
    PAID_TASK_LIMIT: int = int(os.getenv("PAID_TASK_LIMIT", "9999"))
    PAID_TOKEN_BUDGET: int = int(os.getenv("PAID_TOKEN_BUDGET", "10000000"))

    # NEW: demo auth controls
    AUTH_DEMO: bool = os.getenv("AUTH_DEMO", "true").lower() == "true"
    DEMO_TOKEN: str = os.getenv("DEMO_TOKEN", "demo")

    # NEW: JWT settings (for real mode)
    JWT_KEY: str = os.getenv("JWT_KEY", "dev-secret")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    JWT_ISS: str | None = os.getenv("JWT_ISS")
    JWT_AUD: str | None = os.getenv("JWT_AUD")
    JWT_EXPIRE_MIN: int = int(os.getenv("JWT_EXPIRE_MIN", "60"))

settings = Settings()
