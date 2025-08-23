from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conversation_id: str
    status: str
    mode: str
    plan: List[str]
    started_at: str
    finished_at: Optional[str] = None
