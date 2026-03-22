from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from pydantic import BaseModel
from typing import Optional
import fitz  # PyMuPDF
import httpx
import json
import logging
from datetime import datetime
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.syllabus import SyllabusSchema, SyllabusTopic
from app.services.llm import GEMINI_URL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/syllabus", tags=["Syllabus"])

@router.post("/upload")
async def upload_master_syllabus(
    file: UploadFile = File(...), 
    exam_track: str = Form("JEE"),
    exam_date: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # 1. Text Extraction (PyMuPDF)
    try:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        raw_text = ""
        for page in doc:
            raw_text += page.get_text()
    except Exception as e:
        logger.error(f"Failed to read PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read PDF: {str(e)}")
        
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="PDF contains no extractable text.")
        
    # 2. LLM Parsing (Gemini)
    system_instruction = (
        "You are an expert curriculum parser. Extract the chronological syllabus from the provided text. "
        "Return ONLY a valid JSON object with a 'chapters' array. Each item in the array must have a 'topic_name' string. "
        "Keep the exact chronological order as presented in the document."
    )
    
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Extract syllabus from this text:\n\n{raw_text}"}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                GEMINI_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            
        if response.status_code != 200:
            logger.error(f"Gemini API Error: {response.text}")
            raise HTTPException(status_code=502, detail="AI Parsing failed")
            
        data = response.json()
        candidate = data.get("candidates", [{}])[0]
        llm_response_text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Parse the JSON response
        llm_response_text = llm_response_text.strip()
        if llm_response_text.startswith("```json"):
            llm_response_text = llm_response_text[7:]
        if llm_response_text.endswith("```"):
            llm_response_text = llm_response_text[:-3]
            
        parsed_chapters = json.loads(llm_response_text.strip())
        chapters_list = parsed_chapters.get("chapters", [])
        
    except Exception as e:
        logger.error(f"LLM Parsing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to parse syllabus with AI.")
        
    # 3. Database Operations
    db = get_database()
    
    try:
        topics = [SyllabusTopic(topic_name=item["topic_name"]) for item in chapters_list if "topic_name" in item]
        syllabus_obj = SyllabusSchema(
            user_id=str(user_id),
            exam_track=exam_track,
            chapters=topics
        )
        
        syllabus_dict = syllabus_obj.model_dump(by_alias=True, exclude_none=True)
        if "_id" not in syllabus_dict or syllabus_dict["_id"] is None:
             syllabus_dict["_id"] = ObjectId()
        elif isinstance(syllabus_dict.get("_id"), str):
             syllabus_dict["_id"] = ObjectId(syllabus_dict["_id"])
             
        insert_result = await db.syllabuses.insert_one(syllabus_dict)
        inserted_id = insert_result.inserted_id
        
        update_fields = {
            "master_syllabus_id": str(inserted_id),
            "exam_track": exam_track
        }
        
        if exam_date:
            try:
                update_fields["exam_date"] = datetime.strptime(exam_date, "%Y-%m-%d")
            except ValueError:
                pass # ignore if format is somewhat invalid
                
        await db.users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": update_fields}
        )
        
        # Convert _id to string for JSON serialization
        syllabus_dict["_id"] = str(syllabus_dict["_id"])
        
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save syllabus to database.")
        
    return {
        "message": "Master Syllabus uploaded and parsed successfully",
        "data": syllabus_dict
    }

class CompleteChapterRequest(BaseModel):
    topic_name: str

@router.get("/my-roadmap")
async def get_my_roadmap(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = current_user["user_id"]
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("master_syllabus_id"):
        return {"data": None}
        
    syllabus = await db.syllabuses.find_one({"_id": ObjectId(user["master_syllabus_id"])})
    if not syllabus:
        return {"data": None}
        
    # Serialize ID for json response
    syllabus["_id"] = str(syllabus["_id"])
    return {"data": syllabus}

@router.patch("/complete-chapter")
async def complete_chapter(request: CompleteChapterRequest, current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = current_user["user_id"]
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("master_syllabus_id"):
        raise HTTPException(status_code=404, detail="User roadmap not found")
        
    # 1. Update the syllabus tracking
    update_result = await db.syllabuses.update_one(
        {
            "_id": ObjectId(user["master_syllabus_id"]),
            "chapters.topic_name": request.topic_name
        },
        {
            "$set": {
                "chapters.$.is_completed": True,
                "chapters.$.completed_at": datetime.utcnow()
            }
        }
    )
    
    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Chapter not found or already completed")
        
    # 2. Add to the user's covered_topics array
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"covered_topics": request.topic_name}}
    )
    
    return {"message": "Chapter marked as complete successfully"}
