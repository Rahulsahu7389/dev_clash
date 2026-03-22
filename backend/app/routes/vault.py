from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from typing import List
from datetime import datetime
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.services.rag import (
    process_and_store_pdf,
    generate_vault_answer,
    generate_practice_from_scratchpad
)
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
    
    result = await process_and_store_pdf(file, user_id)
    return result

@router.post("/ask")
async def ask_question(request: AskRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    return await generate_vault_answer(
        question=request.question,
        active_doc_ids=request.active_doc_ids,
        socratic_mode=request.socratic_mode,
        user_id=user_id
    )

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
