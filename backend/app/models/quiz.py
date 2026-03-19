from pydantic import BaseModel, Field
from typing import List


class QuizGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="The topic to generate quiz questions for")


class MCQItem(BaseModel):
    question: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_answer: str
    explanation: str


class QuizSubmitRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    quality: int = Field(..., ge=0, le=5, description="Recall quality: 0 (blackout) to 5 (perfect)")
