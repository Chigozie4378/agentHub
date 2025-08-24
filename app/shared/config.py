from pydantic import BaseModel
import os

class Settings(BaseModel):
    ENV: str = os.getenv("ENV", "dev")
    DEFAULT_TIER: str = os.getenv("DEFAULT_TIER", "free")
    FREE_TASK_LIMIT: int = int(os.getenv("FREE_TASK_LIMIT", "50"))
    FREE_TOKEN_BUDGET: int = int(os.getenv("FREE_TOKEN_BUDGET", "200000"))
    PAID_TASK_LIMIT: int = int(os.getenv("PAID_TASK_LIMIT", "9999"))
    PAID_TOKEN_BUDGET: int = int(os.getenv("PAID_TOKEN_BUDGET", "10000000"))

    # --- NEW: Browser engine selection ---
    # auto | playwright | cli
    BROWSER_ENGINE: str = os.getenv("BROWSER_ENGINE", "auto")
    # Optional absolute path to chrome/msedge (for CLI fallback)
    CHROME_PATH: str | None = os.getenv("CHROME_PATH")

settings = Settings()
