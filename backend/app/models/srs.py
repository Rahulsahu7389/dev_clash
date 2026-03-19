from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SRSRecordSchema(BaseModel):
    user_id: str
    topic: str
    ease_factor: float = 2.5
    interval: int = 0
    next_review_date: datetime = Field(default_factory=datetime.utcnow)
