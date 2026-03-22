from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from datetime import datetime, timezone
from typing import List

from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.models.quiz import VaultHistorySchema
from app.services.llm import extract_topics

router = APIRouter(prefix="/vault", tags=["Study Vault"])

@router.post("/process", response_model=VaultHistorySchema)
async def process_vault_item(
    source_reference: str,
    source_type: str,
    content: str, # For now assuming text content is passed after processing (e.g. OCR)
    current_user: dict = Depends(get_current_user)
):
    """
    Process educational text from a source (PDF/Video), extract academic topics,
    and save to vault history for future recommendations.
    """
    db = get_database()
    user_id = current_user["user_id"]
    
    # ── Step 1: AI Extract Topics from Processed Text ──
    try:
        topics = await extract_topics(content)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Topic extraction failed: {str(e)}")

    # ── Step 2: Create Vault History Record ──
    vault_item = VaultHistorySchema(
        user_id=user_id,
        source_reference=source_reference,
        source_type=source_type,
        extracted_topics=topics,
        created_at=datetime.now(timezone.utc)
    )
    
    # ── Step 3: Insert into MongoDB ──
    await db.vault_history.insert_one(vault_item.dict(by_alias=True))
    
    return vault_item
