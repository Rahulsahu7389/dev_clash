from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.common import PyObjectId

ALLOWED_TRACKS = ["JEE", "NEET", "UPSC", "GATE"]

class UserSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    email: EmailStr
    hashed_password: str
    role: str = "student"
    elo_rating: int = 1200
    total_xp: int = 0
    exam_track: str = "JEE"
    
    # NEW Fields for Progression Tracking:
    exam_date: Optional[datetime] = None
    master_syllabus_id: Optional[str] = None
    covered_topics: List[str] = Field(default_factory=list, description="List of topics the user has completed")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    exam_track: str

    @field_validator('exam_track')
    @classmethod
    def validate_exam_track(cls, v):
        if v not in ALLOWED_TRACKS:
            raise ValueError(f"exam_track must be one of {ALLOWED_TRACKS}")
        return v

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None
