from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.user import UserSchema
from app.models.srs import SRSRecordSchema
from app.models.quiz import MCQItem, QuizResponseItem
from app.services.llm import generate_mcqs

router = APIRouter(prefix="/mock-test", tags=["Mock Test"])

class QuizSubmitRequest(BaseModel):
    user_id: str
    score: int
    warnings_issued: int
    total_questions: int
    responses: List[QuizResponseItem]
    completed_at: Optional[datetime] = None

@router.get("/generate/{user_id}")
async def generate_mock_test(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Generate a 5-question mock test based on the topics the user has covered/unlocked.
    """
    db = get_database()
    
    # 1. Fetch User
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    covered_topics = user.get("covered_topics", [])
    if not covered_topics:
        raise HTTPException(
            status_code=400, 
            detail="Please complete at least one chapter on your dashboard."
        )
        
    # 2. Generate questions from covered topics
    # We pass the list of topics as a single descriptor string
    topic_context = ", ".join(covered_topics)
    exam_track = user.get("exam_track", "JEE")
    
    try:
        # We reuse the existing generate_mcqs but can wrap it to ensure strictness if needed.
        # For now, generate_mcqs already asks to mirror the exam track.
        questions_raw = await generate_mcqs(topic_context, exam_track)
        
        # Ensure only 5 questions
        questions_raw = questions_raw[:5]
        
        return {
            "user_id": user_id,
            "topics_queried": covered_topics,
            "questions": questions_raw
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate mock test: {str(e)}"
        )

@router.post("/submit")
async def submit_mock_test(request: QuizSubmitRequest, current_user: dict = Depends(get_current_user)):
    """
    Submit test results, update XP/Stats, and trigger SRS for mistakes.
    """
    db = get_database()
    user_id = request.user_id
    
    # 1. Update User Stats (Gamification)
    # Give XP based on score (e.g., 20 XP per correct answer)
    xp_gained = request.score * 20
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"total_xp": xp_gained}}
    )
    
    # 2. The SRS Loop: Handle Mistakes
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    
    srs_updates = 0
    for resp in request.responses:
        if not resp.is_correct:
            # We use the topic_name from the response item to create an SRS record
            topic = resp.topic_name or "General Problem"
            
            # SM-2: Reset on mistake (interval=1, which is the immediate next day for review)
            srs_record = {
                "user_id": user_id,
                "reference_id": topic,
                "record_type": "topic",
                "interval": 1,
                "repetition_count": 0,
                "ease_factor": 2.5,
                "last_reviewed_date": datetime.now(timezone.utc),
                "next_review_date": tomorrow
            }
            
            await db.srs_records.update_one(
                {"user_id": user_id, "reference_id": topic, "record_type": "topic"},
                {"$set": srs_record},
                upsert=True
            )
            srs_updates += 1
            
    return {
        "message": "Results recorded successfully",
        "xp_gained": xp_gained,
        "warnings_issued": request.warnings_issued,
        "srs_entries_created": srs_updates
    }
