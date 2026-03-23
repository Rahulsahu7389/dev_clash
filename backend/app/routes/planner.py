from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.services.llm import generate_daily_plan

router = APIRouter(prefix="/planner", tags=["Planner"])

@router.get("/daily", response_model=List[Dict[str, Any]])
async def get_daily_plan(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    db = get_database()
    today = datetime.now(timezone.utc)
    
    # 1. Exam Date & Days Remaining
    try:
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user_doc = None
        
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
        
    exam_date = user_doc.get("exam_date")
    days_remaining = 30
    
    if isinstance(exam_date, str):
        try:
            exam_date = datetime.fromisoformat(exam_date.replace('Z', '+00:00'))
        except ValueError:
            exam_date = None
            
    if isinstance(exam_date, datetime):
        if exam_date.tzinfo is None:
            exam_date = exam_date.replace(tzinfo=timezone.utc)
        days_remaining = max(0, (exam_date - today).days)
        
    # 2. Fetch pending syllabus
    pending_topics = []
    syllabus_doc = await db.syllabus.find_one({
        "user_id": {"$in": [user_id, ObjectId(user_id)]}
    })
    
    if syllabus_doc and "topics" in syllabus_doc:
        for topic in syllabus_doc["topics"]:
            if not topic.get("is_completed", False):
                pending_topics.append(topic.get("name", "Unknown Topic"))
                if len(pending_topics) >= 3:
                    break
                    
    # 3. Fetch Urgent Decays
    srs_cursor = db.srs_records.find({
        "user_id": {"$in": [user_id, ObjectId(user_id)]},
        "next_review_date": {"$lte": today}
    }).limit(3)
    
    srs_records = await srs_cursor.to_list(length=3)
    urgent_srs = [record.get("reference_id") for record in srs_records if record.get("reference_id")]
    
    # 4. LLM Call
    daily_plan = await generate_daily_plan(
        days_remaining=days_remaining,
        pending_topics=pending_topics,
        urgent_srs=urgent_srs
    )
    
    return daily_plan
