from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    mime: str
    size: int
    sha256: str
    created_at: datetime

class SignedUrlOut(BaseModel):
    url: str
    expires_at: datetime
