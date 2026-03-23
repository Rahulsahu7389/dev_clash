from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from app.core.database import get_database
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics", response_model=Dict[str, Any])
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    db = get_database()
    today = datetime.now(timezone.utc)
    
    # 1. User Stats
    try:
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user_doc = None
        
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
        
    username = user_doc.get("username", "Scholar")
    total_xp = user_doc.get("xp", 0)  
    elo_rating = user_doc.get("elo_rating", 1200)
    level = int(total_xp / 500) + 1
    exam_track = user_doc.get("exam_track", "JEE")
    
    # 2. Daily Activity Heatmap (Last 28 days)
    heatmap = []
    for i in range(27, -1, -1):
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        start_of_day = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)
        
        # We query activity_logs correctly
        action_count = await db.activity_logs.count_documents({
            "user_id": {"$in": [user_id, ObjectId(user_id)]},
            "timestamp": {"$gte": start_of_day, "$lt": end_of_day}
        })
        
        heatmap.append({"date": date_str, "count": action_count})
        
    # 3. Targeted Mastery (Radar)
    srs_cursor = db.srs_records.find({
        "user_id": {"$in": [user_id, ObjectId(user_id)]}
    })
    srs_list = await srs_cursor.to_list(length=500)
    
    mastery_radar = []
    if srs_list:
        categories = {"Physics": [], "Chemistry": [], "Math": [], "Logic": [], "Accuracy": []}
        for rec in srs_list:
            ef = rec.get("ease_factor", 2.5)
            # Normalize EF: 2.5 typical -> 80% mark
            normalized = min(100, max(0, int((ef / 3.125) * 100))) 
            topic = rec.get("reference_id", "").lower()
            
            if "phys" in topic or "kinematics" in topic or "mechanics" in topic:
                categories["Physics"].append(normalized)
            elif "chem" in topic or "atom" in topic or "reaction" in topic:
                categories["Chemistry"].append(normalized)
            elif "math" in topic or "calc" in topic or "algebra" in topic:
                categories["Math"].append(normalized)
            elif "logic" in topic or "reasoning" in topic:
                categories["Logic"].append(normalized)
            else:
                categories["Accuracy"].append(normalized)
            
        for cat, vals in categories.items():
            avg = sum(vals) // len(vals) if vals else 40
            mastery_radar.append({"subject": cat, "A": avg, "fullMark": 100})
    else:
        # Default starting stats
        mastery_radar = [
            {"subject": "Physics", "A": 40, "fullMark": 100},
            {"subject": "Chemistry", "A": 40, "fullMark": 100},
            {"subject": "Math", "A": 40, "fullMark": 100},
            {"subject": "Logic", "A": 40, "fullMark": 100},
            {"subject": "Accuracy", "A": 40, "fullMark": 100},
        ]
        
    return {
        "username": username,
        "total_xp": total_xp,
        "elo_rating": elo_rating,
        "level": level,
        "exam_track": exam_track,
        "heatmap": heatmap,
        "mastery_radar": mastery_radar
    }
