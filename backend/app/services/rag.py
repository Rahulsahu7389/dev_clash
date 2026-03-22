import os
import asyncio
import uuid
import httpx
import logging
import fitz  # PyMuPDF
from datetime import datetime
from fastapi import UploadFile, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.core.database import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)

# Get or create collection
collection = chroma_client.get_or_create_collection(
    name="vault_docs",
    metadata={"hnsw:space": "cosine"}
)

async def _embed_batch(chunks: list[str]) -> list[list[float]]:
    """Get batch embeddings from Gemini API with exponential backoff."""
    # STRICTLY use the active gemini-embedding-001 model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={settings.GEMINI_API_KEY}"
    
    requests = []
    for chunk in chunks:
        requests.append({
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": chunk}]}
        })
        
    payload = {"requests": requests}
    retry_delay = 2.0
    
    for attempt in range(5):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    return [emb.get("values", []) for emb in data.get("embeddings", [])]
                    
                elif response.status_code == 429:
                    logger.warning(f"Rate limit (429). Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    
                else:
                    logger.error(f"Embedding error {response.status_code}: {response.text}")
                    if response.status_code in [400, 404]:
                        return None
                        
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    
        except Exception as e:
            logger.error(f"Embedding exception: {e}")
            await asyncio.sleep(retry_delay)
            retry_delay *= 2
            
    return None

async def process_and_store_pdf(file: UploadFile, user_id: str):
    doc_id = str(uuid.uuid4())
    filename = file.filename
    
    # 1. Extract text
    try:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")
        
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text.strip():
            pages.append({"page": page_num + 1, "text": text})
            
    if not pages:
        raise HTTPException(status_code=400, detail="PDF contains no extractable text.")

    # 2. Split text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    all_chunks = []
    all_metadatas = []
    all_ids = []

    for p in pages:
        page_chunks = splitter.split_text(p["text"])
        for i, chunk in enumerate(page_chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "doc_id": doc_id,
                "doc_name": filename,
                "page": p["page"],
                "user_id": user_id
            })
            all_ids.append(f"{doc_id}_{p['page']}_{i}")

    # 3. Process in batches of 100
    docs_to_insert = []
    metadatas = []
    ids = []
    embeddings = []
    
    batch_size = 100
    total_chunks = len(all_chunks)

    for i in range(0, total_chunks, batch_size):
        chunk_batch = all_chunks[i:i+batch_size]
        meta_batch = all_metadatas[i:i+batch_size]
        id_batch = all_ids[i:i+batch_size]
        
        batch_embs = await _embed_batch(chunk_batch)
        
        if batch_embs is None:
            raise HTTPException(
                status_code=503, 
                detail=f"Google API is currently overloaded. Embedded {len(docs_to_insert)} out of {total_chunks} chunks. Please try uploading again in a minute."
            )
            
        for chunk, meta, cid, emb in zip(chunk_batch, meta_batch, id_batch, batch_embs):
            if emb:
                docs_to_insert.append(chunk)
                metadatas.append(meta)
                ids.append(cid)
                embeddings.append(emb)

        logger.info(f"Embedded batch {i} to {i+len(chunk_batch)}...")
        # Mandatory pacing length limit
        await asyncio.sleep(2.0)

    # 4. Storage in ChromaDB
    if docs_to_insert:
        collection.add(
            documents=docs_to_insert,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

    # 5. Metadata to MongoDB
    db = get_database()
    upload_doc = {
        "doc_id": doc_id,
        "doc_name": filename,
        "uploaded_at": datetime.utcnow().isoformat()
    }
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"vault_documents": upload_doc}}
    )

    return {"message": "Document uploaded successfully", "doc_id": doc_id, "doc_name": filename}

async def generate_vault_answer(question: str, active_doc_ids: list[str], socratic_mode: bool, user_id: str) -> dict:
    # 1. Semantic Search
    question_embs = await _embed_batch([question])
    
    if not question_embs or not question_embs[0]:
        raise HTTPException(status_code=500, detail="Failed to embed question")
        
    question_embedding = question_embs[0]
        
    query_results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5,
        where={"doc_id": {"$in": active_doc_ids}} if active_doc_ids else None
        # Could also filter by user_id to ensure security
    )
    
    context_chunks = []
    if query_results["documents"] and len(query_results["documents"]) > 0:
        docs = query_results["documents"][0]
        meta = query_results["metadatas"][0]
        for d, m in zip(docs, meta):
            context_chunks.append(f"Context from {m['doc_name']} Page {m['page']}:\n{d}")
            
    context_text = "\n\n---\n\n".join(context_chunks)
    
    # 2. Prompt Engineering
    if not socratic_mode:
        system_instruction = (
            "You are an AI assistant. Answer the user's question using ONLY the provided context chunks. "
            "IMPORTANT: Immediately after stating a fact from the context, add a citation tag EXACTLY like this: [DocName, Page X]. "
            "Do NOT include square brackets for anything else except citations."
        )
    else:
        system_instruction = (
            "You are a Socratic Tutor. Do NOT give the final answer. "
            "Analyze the provided context and ask a leading question to guide the student to the answer themselves. "
            "Add a citation tag EXACTLY like this: [DocName, Page X] when referencing context."
        )
        
    # JSON schema output
    system_instruction += (
        "\n\nYou MUST return a valid JSON object with EXACTLY this structure. "
        "Update the graph generation instructions to strictly follow this 4-level hierarchy:\n"
        "Level 1: The Source Document (Connects to Level 2)\n"
        "Level 2: Core Subjects/Categories (e.g., 'Physics'). (Connects to Level 3)\n"
        "Level 3: Specific Topics (e.g., 'Newton\\'s Second Law'). (Connects to Level 4)\n"
        "Level 4: Formulas or Key Definitions (e.g., 'F = ma').\n"
        "{\n"
        '  "answer": "Detailed markdown explanation with [DocName, Page X] citations.",\n'
        '  "concept_nodes": [\n'
        '    {"id": "doc_1", "label": "Document Name"},\n'
        '    {"id": "phys", "label": "Physics"},\n'
        '    {"id": "newt_2", "label": "Newton\'s Second Law", "formula_or_detail": "F = ma"}\n'
        '  ],\n'
        '  "concept_edges": [{"source": "Concept1", "target": "DocName", "label": "found in"}]\n'
        "}\n"
        "Ensure the JSON is strictly valid."
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Context:\n{context_text}\n\nQuestion:\n{question}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.3 if not socratic_mode else 0.7,
            "responseMimeType": "application/json"
        }
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, json=payload)
        
    if response.status_code != 200:
         raise HTTPException(status_code=500, detail=f"LLM API error: {response.text}")
         
    try:
        data = response.json()
        raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        import re, json
        # Extract JSON block between first { and last }
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            raw_text = match.group(0)
            
        result = json.loads(raw_text)
        return result
    except Exception as e:
        logger.error(f"Failed to parse Vault answer JSON: {e} | Raw Text: {raw_text}")
        raise HTTPException(status_code=500, detail="Failed to parse structured answer from AI")

async def generate_practice_from_scratchpad(text: str, user_id: str) -> dict:
    system_instruction = (
        "You are an expert examiner. Generate exactly 3 Multiple Choice Questions (MCQs) based on the provided text. "
        "Keep the explanation concise. Output ONLY a valid JSON array of exactly 3 objects with this structure:\n"
        '[{"question": "Q?", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "Why"}]'
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "temperature": 0.5,
            "responseMimeType": "application/json"
        }
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
             raise HTTPException(status_code=500, detail=f"LLM API error: {response.text}")
             
    try:
        data = response.json()
        raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        import re, json
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if match:
            raw_text = match.group(0)
            
        mcqs = json.loads(raw_text)
        
        db = get_database()
        # Save to user's SRS queue or arena practice queue
        # For simplicity we'll append to an `srs_queue` array
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"srs_queue": {"$each": mcqs}}}
        )
        return {"message": "Practice questions generated successfully", "mcqs": mcqs}
    except Exception as e:
        logger.error(f"Failed to generate practice: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate practice questions")