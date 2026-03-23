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
    try:
        # --- SAFE ID EXTRACTION ---
        if hasattr(current_user, "id"):
            user_id_str = str(current_user.id)
        elif isinstance(current_user, dict):
            # Added "user_id" lookup since get_current_user yields "user_id" 
            user_id_str = str(current_user.get("user_id") or current_user.get("id") or current_user.get("_id"))
        else:
            user_id_str = str(current_user)
        # --------------------------
        
        if not user_id_str or user_id_str == "None":
            raise HTTPException(status_code=401, detail="Unauthorized")

        db = get_database()
        
        try:
            obj_id = ObjectId(user_id_str)
        except Exception:
            obj_id = user_id_str

        # 1. Safe Exam Date Calculation
        # Re-attached user_doc fetch since get_current_user only gives ID and role
        try:
            user_doc = await db.users.find_one({"_id": obj_id})
        except Exception:
            user_doc = {}
            
        if not user_doc:
            user_doc = {}

        days_remaining = 30 # Default to 30 days if None
        exam_date = user_doc.get("exam_date") or current_user.get("exam_date")
        
        if exam_date:
            if isinstance(exam_date, str):
                try:
                    exam_date = datetime.fromisoformat(exam_date.replace('Z', '+00:00'))
                except ValueError:
                    exam_date = None
            # Ensure timezone awareness before subtracting
            now = datetime.now(timezone.utc)
            if isinstance(exam_date, datetime):
                if exam_date.tzinfo is None:
                    exam_date = exam_date.replace(tzinfo=timezone.utc)
                days_remaining = max(0, (exam_date - now).days)

        # 2. Safe Syllabus Fetch
        syllabus = await db.syllabus.find_one({"user_id": {"$in": [user_id_str, obj_id]}})
        pending_topics = []
        if syllabus:
            if "chapters" in syllabus:
                pending_topics = [ch.get("topic_name") for ch in syllabus["chapters"] if not ch.get("is_completed")][:3]
            elif "topics" in syllabus:
                pending_topics = [ch.get("name") for ch in syllabus["topics"] if not ch.get("is_completed")][:3]
        
        pending_topics = [t for t in pending_topics if t]
        if not pending_topics:
            pending_topics = ["General Concepts"] # Fallback

        # 3. Safe SRS Fetch
        srs_cursor = db.srs_records.find({
            "user_id": {"$in": [user_id_str, obj_id]}, 
            "next_review_date": {"$lte": datetime.now(timezone.utc)}
        }).limit(3)
        srs_records = await srs_cursor.to_list(length=3)
        urgent_srs = [r.get("reference_id") for r in srs_records if r.get("reference_id")]

        # 4. Generate AI Plan
        print(f"--- [DEBUG] SENDING TO GEMINI ---")
        print(f"Days: {days_remaining}, Pending: {pending_topics}, Urgent: {urgent_srs}")
        
        plan = await generate_daily_plan(days_remaining, pending_topics, urgent_srs)
        return plan
        
    except Exception as e:
        print(f"--- [CRITICAL ERROR IN /planner/daily] ---")
        print(f"Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return [{
            "task_title": "Setup Required",
            "reasoning": "We need more data to generate your AI plan.",
            "action_type": "vault_study",
            "target_topic": "General Syllabus"
        }]
