from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from typing import List

from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.quiz import QuizGenerateRequest, MCQItem, QuizSubmitRequest
from app.utils.srs import calculate_next_review
from app.services.llm import generate_mcqs

router = APIRouter(prefix="/quiz", tags=["Quiz & SRS"])


@router.post("/generate", response_model=List[MCQItem])
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate 5 MCQs for the given topic using AI.
    Requires a valid JWT token.
    """
    try:
        questions = await generate_mcqs(request.topic)
        return questions
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@router.post("/submit", response_model=dict)
async def submit_quiz(
    request: QuizSubmitRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a quiz result. This:
    1. Looks up or creates the user's SRS record for the topic.
    2. Runs the SM-2 algorithm to compute the next review schedule.
    3. Upserts the SRS record in MongoDB.
    4. Upserts the daily activity log (for the GitHub-style heatmap).
    """
    db = get_database()
    user_id = current_user["user_id"]
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # --- Step 1: Find or default SRS record for this topic ---
    srs_record = await db.srs_records.find_one(
        {"user_id": user_id, "topic": request.topic}
    )

    current_ease_factor = srs_record["ease_factor"] if srs_record else 2.5
    current_interval = srs_record["interval"] if srs_record else 0

    # --- Step 2: Apply SM-2 algorithm ---
    srs_result = calculate_next_review(
        quality=request.quality,
        ease_factor=current_ease_factor,
        interval=current_interval
    )

    # --- Step 3: Upsert SRS record ---
    await db.srs_records.update_one(
        {"user_id": user_id, "topic": request.topic},
        {
            "$set": {
                "user_id": user_id,
                "topic": request.topic,
                "ease_factor": srs_result["ease_factor"],
                "interval": srs_result["interval"],
                "next_review_date": srs_result["next_review_date"],
            }
        },
        upsert=True
    )

    # --- Step 4: Upsert activity log (increment actions_completed for today) ---
    await db.activity_logs.update_one(
        {"user_id": user_id, "date": today_str},
        {
            "$inc": {"actions_completed": 1},
            "$setOnInsert": {"user_id": user_id, "date": today_str}
        },
        upsert=True
    )

    return {
        "message": "Quiz submitted successfully",
        "topic": request.topic,
        "next_review_in_days": srs_result["interval"],
        "next_review_date": srs_result["next_review_date"].strftime("%Y-%m-%d"),
        "ease_factor": srs_result["ease_factor"],
    }


@router.get("/daily", response_model=List[str])
async def get_daily_review(
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of topics due for review today.
    Queries srs_records where next_review_date <= now (UTC).
    """
    db = get_database()
    user_id = current_user["user_id"]
    now_utc = datetime.now(timezone.utc)

    cursor = db.srs_records.find(
        {
            "user_id": user_id,
            "next_review_date": {"$lte": now_utc}
        },
        {"topic": 1, "_id": 0}  # Project only the topic field
    )

    due_records = await cursor.to_list(length=100)
    topics_due = [record["topic"] for record in due_records]

    return topics_due
