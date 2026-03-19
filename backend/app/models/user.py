from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from app.models.common import PyObjectId

class UserSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    email: EmailStr
    hashed_password: str
    role: str = "student"
    elo_rating: int = 1200
    total_xp: int = 0
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None
