from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.common import PyObjectId

class SyllabusTopic(BaseModel):
    topic_name: str
    is_completed: bool = False
    completed_at: Optional[datetime] = None

class SyllabusSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    exam_track: str
    chapters: List[SyllabusTopic]
    created_at: datetime = Field(default_factory=datetime.utcnow)
