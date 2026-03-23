# from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
# from typing import List
# from datetime import datetime
# from pydantic import BaseModel
# from app.core.dependencies import get_current_user
# from app.services.rag import (
#     process_and_store_pdf,
#     generate_vault_answer,
#     generate_practice_from_scratchpad
# )
# from app.core.database import get_database
# from bson import ObjectId

# router = APIRouter(prefix="/vault", tags=["Vault"])

# class AskRequest(BaseModel):
#     question: str
#     active_doc_ids: List[str]
#     socratic_mode: bool = False

# class PracticeRequest(BaseModel):
#     text: str

# class ScratchpadRequest(BaseModel):
#     text: str

# @router.post("/upload")
# async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
#     user_id = current_user["user_id"]
#     if not file.filename.lower().endswith('.pdf'):
#         raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
#     result = await process_and_store_pdf(file, user_id)
#     return result

# @router.post("/ask")
# async def ask_question(request: AskRequest, current_user: dict = Depends(get_current_user)):
#     user_id = current_user["user_id"]
#     return await generate_vault_answer(
#         question=request.question,
#         active_doc_ids=request.active_doc_ids,
#         socratic_mode=request.socratic_mode,
#         user_id=user_id
#     )

# @router.post("/generate-practice")
# async def generate_practice(request: PracticeRequest, current_user: dict = Depends(get_current_user)):
#     user_id = current_user["user_id"]
#     return await generate_practice_from_scratchpad(request.text, user_id)

# @router.get("/documents")
# async def get_documents(current_user: dict = Depends(get_current_user)):
#     db = get_database()
#     user_id = current_user["user_id"]
#     user = await db.users.find_one({"_id": ObjectId(user_id)}, {"vault_documents": 1})
#     if not user:
#          raise HTTPException(status_code=404, detail="User not found")
         
#     return user.get("vault_documents", [])

# @router.post("/scratchpad")
# async def save_scratchpad(request: ScratchpadRequest, current_user: dict = Depends(get_current_user)):
#     user_id = current_user["user_id"]
#     db = get_database()
#     note = {
#         "text": request.text,
#         "created_at": datetime.utcnow().isoformat()
#     }
#     await db.users.update_one(
#         {"_id": ObjectId(user_id)},
#         {"$push": {"scratchpad_notes": note}}
#     )
#     return {"message": "Note saved", "note": note}

# @router.get("/scratchpad")
# async def get_scratchpad(current_user: dict = Depends(get_current_user)):
#     db = get_database()
#     user_id = current_user["user_id"]
#     user = await db.users.find_one({"_id": ObjectId(user_id)}, {"scratchpad_notes": 1})
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
        
#     return {"notes": user.get("scratchpad_notes", [])}


from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from app.utils.activity import log_user_activity
from typing import List
from datetime import datetime, timedelta
from app.models.srs import SRSRecordSchema
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.services.rag import (
    process_and_store_pdf,
    generate_vault_answer,
    generate_practice_from_scratchpad
)
from app.services.llm import extract_pdf_topics
import fitz # PyMuPDF
from app.core.database import get_database
from bson import ObjectId

router = APIRouter(prefix="/vault", tags=["Vault"])

class AskRequest(BaseModel):
    question: str
    active_doc_ids: List[str]
    socratic_mode: bool = False

class PracticeRequest(BaseModel):
    text: str

class ScratchpadRequest(BaseModel):
    text: str

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # 1. Existing PYQ and storage logic (Do not touch)
    result = await process_and_store_pdf(file, user_id)
    doc_id = result.get("doc_id")

    # 2. SILENT TOPIC EXTRACTION (New Addition)
    try:
        # Seek back to start of file to extract text for the new LLM call
        await file.seek(0)
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Call the new isolated LLM function
        topics = await extract_pdf_topics(full_text)
        
        if topics:
            db = get_database()
            
            # Save to vault_sources (to link topics to source as requested)
            await db.vault_sources.update_one(
                {"source_id": doc_id},
                {
                    "$set": {
                        "user_id": ObjectId(user_id),
                        "source_name": file.filename,
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # Save to user_topics (linking topics to user and source)
            # Using $addToSet to prevent duplication for the user
            await db.user_topics.update_one(
                {"user_id": ObjectId(user_id)},
                {
                    "$addToSet": {"topics": {"$each": topics}},
                    "$set": {"last_updated": datetime.utcnow()}
                },
                upsert=True
            )
            
            # Track the specific topics for THIS specific document in a separate relationship collection or nested
            await db.source_topics.insert_one({
                "source_id": doc_id,
                "user_id": ObjectId(user_id),
                "topics": topics,
                "extracted_at": datetime.utcnow()
            })

    except Exception as e:
        # Fail silently as requested ("silently extract") to not break the working upload
        print(f"Silent topic extraction failed: {str(e)}")

    return result

@router.post("/ask")
async def ask_question(request: AskRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    answer_result = await generate_vault_answer(
        question=request.question,
        active_doc_ids=request.active_doc_ids,
        socratic_mode=request.socratic_mode,
        user_id=user_id
    )
    
    db = get_database()
    now = datetime.utcnow()
    
    # 2. Intercept Vault Chats: fetch topics associated with active_doc_ids
    if request.active_doc_ids:
        source_records = await db.source_topics.find({
            "source_id": {"$in": request.active_doc_ids},
            "user_id": ObjectId(user_id)
        }).to_list(length=None)
        
        topics_to_update = set()
        for record in source_records:
            for topic in record.get("topics", []):
                topics_to_update.add(topic)
                
        # Update srs_records for each topic
        for topic in topics_to_update:
            existing_record = await db.srs_records.find_one({
                "user_id": user_id,
                "reference_id": topic,
                "record_type": "topic"
            })
            
            if existing_record:
                await db.srs_records.update_one(
                    {"_id": existing_record["_id"]},
                    {
                        "$set": {
                            "last_reviewed_date": now
                        },
                        "$inc": {
                            "repetition_count": 1
                        }
                    }
                )
            else:
                new_record = SRSRecordSchema(
                    user_id=user_id,
                    reference_id=topic,
                    record_type="topic",
                    repetition_count=1,
                    interval=1,
                    ease_factor=2.5,
                    last_reviewed_date=now,
                    next_review_date=now + timedelta(days=1)
                )
                
                await db.srs_records.insert_one(new_record.model_dump(by_alias=True, exclude_none=True))
                
    # 3. Log Chat History
    chat_log = {
        "user_id": ObjectId(user_id),
        "question": request.question,
        "answer": answer_result,
        "active_doc_ids": request.active_doc_ids,
        "socratic_mode": request.socratic_mode,
        "timestamp": now
    }
    await db.vault_chat_logs.insert_one(chat_log)
    
    # --- ACTIVITY LOGGING ---
    await log_user_activity(db, str(user_id))
    
    return answer_result

@router.post("/generate-practice")
async def generate_practice(request: PracticeRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    return await generate_practice_from_scratchpad(request.text, user_id)

@router.get("/documents")
async def get_documents(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = current_user["user_id"]
    user = await db.users.find_one({"_id": ObjectId(user_id)}, {"vault_documents": 1})
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
         
    return user.get("vault_documents", [])

@router.post("/scratchpad")
async def save_scratchpad(request: ScratchpadRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    db = get_database()
    note = {
        "text": request.text,
        "created_at": datetime.utcnow().isoformat()
    }
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"scratchpad_notes": note}}
    )
    return {"message": "Note saved", "note": note}

@router.get("/scratchpad")
async def get_scratchpad(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = current_user["user_id"]
    user = await db.users.find_one({"_id": ObjectId(user_id)}, {"scratchpad_notes": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"notes": user.get("scratchpad_notes", [])}
