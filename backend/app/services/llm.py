# import json
# import os
# import logging
# from typing import List
# from dotenv import load_dotenv
# from fastapi import HTTPException
# from app.services.rag import collection
# from groq import AsyncGroq

# logger = logging.getLogger(__name__)

# # ── Groq API Key & Client ────────────────────────────────────────────────────
# API_KEY =  os.getenv("GEMINI_API_KEY","").strip().strip("'").strip('"')
# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip().strip("'").strip('"')

# if not GROQ_API_KEY:
#     logger.warning("GROQ_API_KEY is not set. Generation will fail.")


# # ── Endpoint ─────────────────────────────────────────────────────────────────
# GEMINI_URL = (
#     "https://generativelanguage.googleapis.com/v1beta/models/"
#     f"gemini-2.5-flash:generateContent?key={API_KEY}"
# )

# # ── System Instruction logic moved inside payload logic ─────────────────────

# # ── Response Schema (REST format) ─────────────────────────────────────────────
# RESPONSE_SCHEMA = {
#     "type": "ARRAY",
#     "items": {
#         "type": "OBJECT",
#         "properties": {
#             "question":       {"type": "STRING"},
#             "options":        {"type": "ARRAY", "items": {"type": "STRING"}},
#             "correct_answer": {"type": "STRING"},
#             "explanation":    {"type": "STRING"},
#         },
#         "required": ["question", "options", "correct_answer", "explanation"],
#     },
# }


# def _build_payload(topic: str, exam_track: str) -> dict:
#     """Construct the full Gemini REST API request payload."""
#     system_instruction = (
#         f"You are an expert, strict examiner for the Indian {exam_track} competitive exam. "
#         f"Generate exactly 5 MCQs on the topic: {topic}. "
#         f"The difficulty, trickiness, and style must perfectly mirror actual past {exam_track} papers. "
#         "The user will provide a mixed list of subjects and topics. You must generate exactly 5 MCQs distributed as evenly as possible across the provided subjects. Do not focus on just one subject. "
#         "Keep the 'explanation' field extremely concise. Maximum 2 sentences per explanation. Do not write lengthy paragraphs. "
#         "Output ONLY a valid JSON array of exactly 5 objects. "
#         "NEVER use unescaped double quotes inside your text strings. "
#         "If you need to quote a term inside a question or explanation, use single quotes instead. "
#         "Do NOT wrap your response in markdown code fences or backticks. "
#         "Do NOT add any text before or after the JSON array. "
#         "Ensure the JSON is perfectly formatted and can be parsed by Python's json.loads()."
#     )
#     return {
#         "system_instruction": {
#             "parts": [{"text": system_instruction}]
#         },
#         "contents": [
#             {
#                 "role": "user",
#                 "parts": [{"text": f"Generate 5 MCQs about: {topic} for {exam_track}"}],
#             }
#         ],
#         "safetySettings": [
#             {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
#         ],
#         "generationConfig": {
#             "temperature":      0.7,
#             "maxOutputTokens":  8192,
#             "responseMimeType": "application/json",
#             "responseSchema":   RESPONSE_SCHEMA,
#         },
#     }


# def _extract_json_array(raw_text: str) -> list:
#     """
#     Bulletproof JSON extractor.

#     Strategy:
#       1. Use regex to find the outermost [...] block — ignores markdown fences
#          and any stray conversational text the model might prepend/append.
#       2. Attempt direct json.loads() on the extracted string.
#       3. If that fails, try a best-effort repair pass before giving up.
#     """
#     # Step 1 — regex: grab everything from first '[' to last ']'
#     match = re.search(r'\[.*\]', raw_text, re.DOTALL)
#     if not match:
#         _log_raw_and_raise(raw_text, "No JSON array found in Gemini response.")

#     json_str = match.group(0)

#     # Step 2 — direct parse
#     try:
#         return json.loads(json_str)
#     except json.JSONDecodeError as primary_err:
#         logger.warning(f"Direct parse failed ({primary_err}). Attempting repair...")

#     # Step 3 — best-effort repair: replace curly/smart quotes, fix newlines
#     repaired = (
#         json_str
#         .replace('\u201c', '\\"').replace('\u201d', '\\"')  # "smart" double quotes
#         .replace('\u2018', "'").replace('\u2019', "'")       # smart single quotes
#         .replace('\r\n', ' ').replace('\n', ' ')             # embedded newlines
#     )
    
#     try:
#         return json.loads(repaired)
#     except json.JSONDecodeError as repair_err:
#         _log_raw_and_raise(raw_text, f"Repair also failed: {repair_err}")


# def _log_raw_and_raise(raw_text: str, reason: str):
#     """Print the full raw response so the broken character is visible, then raise 503."""
#     border = "!" * 70
#     print(f"\n{border}")
#     print("🔥  JSON PARSE FAILURE — FULL RAW GEMINI TEXT BELOW")
#     print(f"REASON : {reason}")
#     print(f"LENGTH : {len(raw_text)} chars")
#     print("RAW TEXT ↓↓↓")
# FALLBACK_MCQS = [
#     {
#         "question": "If a system is in equilibrium, the net force is?",
#         "options": ["Zero", "Maximum", "Minimum", "Infinite"],
#         "correct_answer": "Zero",
#         "explanation": "By definition, equilibrium means zero net force."
#     },
#     {
#         "question": "What is the derivative of e^x with respect to x?",
#         "options": ["x*e^(x-1)", "e^x", "ln(x)", "1/x"],
#         "correct_answer": "e^x",
#         "explanation": "The exponential function e^x is its own derivative."
#     },
#     {
#         "question": "In chemistry, what is the atomic number of Carbon?",
#         "options": ["12", "14", "6", "8"],
#         "correct_answer": "6",
#         "explanation": "Carbon features exactly 6 protons in its nucleus."
#     },
#     {
#         "question": "What is traditionally called the powerhouse of the cell?",
#         "options": ["Nucleus", "Mitochondria", "Ribosome", "Endoplasmic Reticulum"],
#         "correct_answer": "Mitochondria",
#         "explanation": "Mitochondria generate most of the cell's supply of ATP."
#     },
#     {
#         "question": "Which of these is a scalar quantity?",
#         "options": ["Velocity", "Acceleration", "Force", "Speed"],
#         "correct_answer": "Speed",
#         "explanation": "Speed has only magnitude, without a specific direction."
#     }
# ]

# async def generate_mcqs(topic: str, exam_track: str) -> list[dict]:
#     """
#     Calls the Gemini REST API via httpx with up to 3 retries.
#     If generation is interrupted (e.g. MAX_TOKENS) or fails to parse,
#     it automatically retries. If all attempts fail, it returns FALLBACK_MCQS
#     so the players are never stuck on the loading page.
#     """
#     payload = _build_payload(topic, exam_track)
#     import asyncio

#     for attempt in range(3):
#         try:
#             async with httpx.AsyncClient(timeout=90.0) as client:
#                 response = await client.post(
#                     GEMINI_URL,
#                     json=payload,
#                     headers={"Content-Type": "application/json"},
#                 )

#             if response.status_code != 200:
#                 logger.warning(f"Gemini API HTTP Error {response.status_code}: {response.text}")
#                 continue

#             data = response.json()
#             candidate = data.get("candidates", [{}])[0]
#             finish_reason = candidate.get("finishReason")
            
#             if finish_reason and finish_reason != "STOP":
#                 logger.warning(f"Gemini finishReason was {finish_reason} on attempt {attempt + 1}")

#             raw_text: str = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

#             if not raw_text:
#                  logger.warning(f"AI returned empty response on attempt {attempt + 1}")
#                  continue
                 
#             # If the json array was cut off, _extract_json_array will fail and raise exception
#             # which we catch below to retry.
#             mcqs = _extract_json_array(raw_text)

#             if isinstance(mcqs, list) and len(mcqs) > 0:
#                 return mcqs

#         except Exception as e:
#             logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
#             await asyncio.sleep(1)
            
#     # If all 3 attempts fail, return robust fallback
#     logger.error("All 3 LLM attempts failed. Injecting fallback MCQs so the Arena continues securely.")
#     return FALLBACK_MCQS

# def _build_context_payload(context_text: str) -> dict:
#     system_instruction = (
#         "You are an expert examiner. Generate exactly 5 MCQs based STRICTLY on the provided context text. "
#         "Do not use outside knowledge. Output a valid JSON array of 5 objects containing 'question', 'options', 'correct_answer', and 'explanation'."
#     )
#     return {
#         "system_instruction": {
#             "parts": [{"text": system_instruction}]
#         },
#         "contents": [
#             {
#                 "role": "user",
#                 "parts": [{"text": f"Context Text:\n{context_text}"}],
#             }
#         ],
#         "safetySettings": [
#             {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
#         ],
#         "generationConfig": {
#             "temperature":      0.5,
#             "maxOutputTokens":  8192,
#             "responseMimeType": "application/json",
#             "responseSchema":   RESPONSE_SCHEMA,
#         },
#     }

# async def generate_mcqs_from_context(context_text: str) -> list[dict]:
#     payload = _build_context_payload(context_text)
#     import asyncio

#     for attempt in range(3):
#         try:
#             async with httpx.AsyncClient(timeout=90.0) as client:
#                 response = await client.post(
#                     GEMINI_URL,
#                     json=payload,
#                     headers={"Content-Type": "application/json"},
#                 )

#             if response.status_code != 200:
#                 logger.warning(f"Gemini API HTTP Error {response.status_code}: {response.text}")
#                 continue

#             data = response.json()
#             candidate = data.get("candidates", [{}])[0]
#             raw_text: str = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

#             if not raw_text:
#                  continue
                 
#             mcqs = _extract_json_array(raw_text)

#             if isinstance(mcqs, list) and len(mcqs) > 0:
#                 return mcqs

#         except Exception as e:
#             logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
#             await asyncio.sleep(1)
            
#     return FALLBACK_MCQS

# async def generate_vault_mcqs(doc_ids: list[str], track: str) -> list[dict]:
#     # Query ChromaDB to get all text chunks for the checked PDFs
#     results = collection.get(where={"doc_id": {"$in": doc_ids}})
    
#     # Combine the text chunks, slice the string to a maximum of 15,000 characters
#     combined_text = "\n".join(results.get("documents", []))[:15000]
    
#     # Pass this combined_text to Gemini 2.5 Flash
#     system_instruction = (
#         "You are an expert examiner. Generate exactly 5 MCQs based STRICTLY on the provided context text. "
#         "Do not hallucinate outside info. Output a valid JSON array of 5 objects containing 'question', 'options', 'correct_answer', and 'explanation'."
#     )
    
#     payload = {
#         "system_instruction": {
#             "parts": [{"text": system_instruction}]
#         },
#         "contents": [
#             {
#                 "role": "user",
#                 "parts": [{"text": f"Context Text:\n{combined_text}"}],
#             }
#         ],
#         "safetySettings": [
#             {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
#             {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
#         ],
#         "generationConfig": {
#             "temperature":      0.5,
#             "maxOutputTokens":  8192,
#             "responseMimeType": "application/json",
#             "responseSchema":   RESPONSE_SCHEMA,
#         },
#     }
    
#     import asyncio
#     for attempt in range(3):
#         try:
#             async with httpx.AsyncClient(timeout=90.0) as client:
#                 response = await client.post(
#                     GEMINI_URL,
#                     json=payload,
#                     headers={"Content-Type": "application/json"},
#                 )

#             if response.status_code != 200:
#                 logger.warning(f"Gemini API HTTP Error {response.status_code}: {response.text}")
#                 continue

#             data = response.json()
#             candidate = data.get("candidates", [{}])[0]
#             raw_text: str = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

#             if not raw_text:
#                  continue
                 
#             mcqs = _extract_json_array(raw_text)

#             if isinstance(mcqs, list) and len(mcqs) > 0:
#                 return mcqs

#         except Exception as e:
#             logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
#             await asyncio.sleep(1)
            
#     return FALLBACK_MCQS


import json
import os
import re
import httpx
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
from app.services.rag import collection

logger = logging.getLogger(__name__)

# ── API Key ──────────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip("'").strip('"')

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment or .env file.")


# ── Endpoint ─────────────────────────────────────────────────────────────────
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.5-flash:generateContent?key={API_KEY}"
)

# ── System Instruction logic moved inside payload logic ─────────────────────

# ── Response Schema (REST format) ─────────────────────────────────────────────
RESPONSE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "question":       {"type": "STRING"},
            "options":        {"type": "ARRAY", "items": {"type": "STRING"}},
            "correct_answer": {"type": "STRING"},
            "explanation":    {"type": "STRING"},
        },
        "required": ["question", "options", "correct_answer", "explanation"],
    },
}


def _build_payload(topic: str, exam_track: str) -> dict:
    """Construct the full Gemini REST API request payload."""
    system_instruction = (
        f"You are an expert, strict examiner for the Indian {exam_track} competitive exam. "
        f"Generate exactly 5 MCQs on the topic: {topic}. "
        f"The difficulty, trickiness, and style must perfectly mirror actual past {exam_track} papers. "
        "The user will provide a mixed list of subjects and topics. You must generate exactly 5 MCQs distributed as evenly as possible across the provided subjects. Do not focus on just one subject. "
        "Keep the 'explanation' field extremely concise. Maximum 2 sentences per explanation. Do not write lengthy paragraphs. "
        "Output ONLY a valid JSON array of exactly 5 objects. "
        "NEVER use unescaped double quotes inside your text strings. "
        "If you need to quote a term inside a question or explanation, use single quotes instead. "
        "Do NOT wrap your response in markdown code fences or backticks. "
        "Do NOT add any text before or after the JSON array. "
        "Ensure the JSON is perfectly formatted and can be parsed by Python's json.loads()."
    )
    return {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Generate 5 MCQs about: {topic} for {exam_track}"}],
            }
        ],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {
            "temperature":      0.7,
            "maxOutputTokens":  8192,
            "responseMimeType": "application/json",
            "responseSchema":   RESPONSE_SCHEMA,
        },
    }


def _extract_json_array(raw_text: str) -> list:
    """
    Bulletproof JSON extractor.

    Strategy:
      1. Use regex to find the outermost [...] block — ignores markdown fences
         and any stray conversational text the model might prepend/append.
      2. Attempt direct json.loads() on the extracted string.
      3. If that fails, try a best-effort repair pass before giving up.
    """
    # Step 1 — regex: grab everything from first '[' to last ']'
    match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if not match:
        _log_raw_and_raise(raw_text, "No JSON array found in Gemini response.")

    json_str = match.group(0)

    # Step 2 — direct parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as primary_err:
        logger.warning(f"Direct parse failed ({primary_err}). Attempting repair...")

    # Step 3 — best-effort repair: replace curly/smart quotes, fix newlines
    repaired = (
        json_str
        .replace('\u201c', '\\"').replace('\u201d', '\\"')  # "smart" double quotes
        .replace('\u2018', "'").replace('\u2019', "'")       # smart single quotes
        .replace('\r\n', ' ').replace('\n', ' ')             # embedded newlines
    )

    try:
        return json.loads(repaired)
    except json.JSONDecodeError as repair_err:
        _log_raw_and_raise(raw_text, f"Repair also failed: {repair_err}")


def _log_raw_and_raise(raw_text: str, reason: str):
    """Print the full raw response so the broken character is visible, then raise 503."""
    border = "!" * 70
    print(f"\n{border}")
    print("🔥  JSON PARSE FAILURE — FULL RAW GEMINI TEXT BELOW")
    print(f"REASON : {reason}")
    print(f"LENGTH : {len(raw_text)} chars")
    print("RAW TEXT ↓↓↓")
FALLBACK_MCQS = [
    {
        "question": "If a system is in equilibrium, the net force is?",
        "options": ["Zero", "Maximum", "Minimum", "Infinite"],
        "correct_answer": "Zero",
        "explanation": "By definition, equilibrium means zero net force."
    },
    {
        "question": "What is the derivative of e^x with respect to x?",
        "options": ["x*e^(x-1)", "e^x", "ln(x)", "1/x"],
        "correct_answer": "e^x",
        "explanation": "The exponential function e^x is its own derivative."
    },
    {
        "question": "In chemistry, what is the atomic number of Carbon?",
        "options": ["12", "14", "6", "8"],
        "correct_answer": "6",
        "explanation": "Carbon features exactly 6 protons in its nucleus."
    },
    {
        "question": "What is traditionally called the powerhouse of the cell?",
        "options": ["Nucleus", "Mitochondria", "Ribosome", "Endoplasmic Reticulum"],
        "correct_answer": "Mitochondria",
        "explanation": "Mitochondria generate most of the cell's supply of ATP."
    },
    {
        "question": "Which of these is a scalar quantity?",
        "options": ["Velocity", "Acceleration", "Force", "Speed"],
        "correct_answer": "Speed",
        "explanation": "Speed has only magnitude, without a specific direction."
    }
]

async def generate_mcqs(topic: str, exam_track: str) -> list[dict]:
    """
    Calls the Gemini REST API via httpx with up to 3 retries.
    If generation is interrupted (e.g. MAX_TOKENS) or fails to parse,
    it automatically retries. If all attempts fail, it returns FALLBACK_MCQS
    so the players are never stuck on the loading page.
    """
    payload = _build_payload(topic, exam_track)
    import asyncio

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    GEMINI_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code != 200:
                logger.warning(f"Gemini API HTTP Error {response.status_code}: {response.text}")
                continue

            data = response.json()
            candidate = data.get("candidates", [{}])[0]
            finish_reason = candidate.get("finishReason")
            
            if finish_reason and finish_reason != "STOP":
                logger.warning(f"Gemini finishReason was {finish_reason} on attempt {attempt + 1}")

            raw_text: str = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

            if not raw_text:
                 logger.warning(f"AI returned empty response on attempt {attempt + 1}")
                 continue
                 
            # If the json array was cut off, _extract_json_array will fail and raise exception
            # which we catch below to retry.
            mcqs = _extract_json_array(raw_text)

            if isinstance(mcqs, list) and len(mcqs) > 0:
                return mcqs

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            await asyncio.sleep(1)
            
    # If all 3 attempts fail, return robust fallback
    logger.error("All 3 LLM attempts failed. Injecting fallback MCQs so the Arena continues securely.")
    return FALLBACK_MCQS

def _build_context_payload(context_text: str) -> dict:
    system_instruction = (
        "You are an expert examiner. Generate exactly 5 MCQs based STRICTLY on the provided context text. "
        "Do not use outside knowledge. Output a valid JSON array of 5 objects containing 'question', 'options', 'correct_answer', and 'explanation'."
    )
    return {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Context Text:\n{context_text}"}],
            }
        ],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {
            "temperature":      0.5,
            "maxOutputTokens":  8192,
            "responseMimeType": "application/json",
            "responseSchema":   RESPONSE_SCHEMA,
        },
    }

async def generate_mcqs_from_context(context_text: str) -> list[dict]:
    payload = _build_context_payload(context_text)
    import asyncio

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    GEMINI_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code != 200:
                logger.warning(f"Gemini API HTTP Error {response.status_code}: {response.text}")
                continue

            data = response.json()
            candidate = data.get("candidates", [{}])[0]
            raw_text: str = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

            if not raw_text:
                 continue
                 
            mcqs = _extract_json_array(raw_text)

            if isinstance(mcqs, list) and len(mcqs) > 0:
                return mcqs

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            await asyncio.sleep(1)
            
    return FALLBACK_MCQS

# ─────────────────────────────────────────────────────────────────────────────
# NEW: Topic Extraction (Silently extracted after Vault upload)
# ─────────────────────────────────────────────────────────────────────────────

async def extract_pdf_topics(pdf_text: str) -> list[str]:
    """
    Silently extracts core academic/subject topics from the provided PDF text.
    Returns a JSON array of strings.
    """
    system_instruction = (
        "You are an academic analyzer. Extract the top 4-6 core subject topics or tags from this educational text. "
        "Keep topic names concise (e.g., 'Quantum Mechanics', 'Organic Chemistry'). "
        "Output ONLY a valid JSON array of strings. "
        "No markdown code blocks, no preamble."
    )
    
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": f"PDF CONTENT:\n{pdf_text[:10000]}"}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(GEMINI_URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                # Use regex to find the [...] JSON block just in case
                raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                
                import re, json
                match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(0)
                    
                topics = json.loads(raw_text)
                if isinstance(topics, list):
                    return topics
    except Exception as e:
        logger.error(f"Topic extraction failed: {e}")
        
    return []

async def generate_vault_mcqs(doc_ids: list[str], track: str) -> list[dict]:
    if not doc_ids: return FALLBACK_MCQS
    # Query ChromaDB to get all text chunks for the checked PDFs
    results = collection.get(where={"doc_id": {"$in": doc_ids}})
    
    # Combine the text chunks, slice the string to a maximum of 15,000 characters
    combined_text = "\n".join(results.get("documents", []))[:15000]
    
    # Pass this combined_text to Gemini 2.5 Flash
    system_instruction = (
        "You are an expert examiner. Generate exactly 5 MCQs based STRICTLY on the provided context text. "
        "Do not hallucinate outside info. Output a valid JSON array of 5 objects containing 'question', 'options', 'correct_answer', and 'explanation'."
    )
    
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Context Text:\n{combined_text}"}],
            }
        ],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {
            "temperature":      0.5,
            "maxOutputTokens":  8192,
            "responseMimeType": "application/json",
            "responseSchema":   RESPONSE_SCHEMA,
        },
    }
    
    import asyncio
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    GEMINI_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code != 200:
                logger.warning(f"Gemini API HTTP Error {response.status_code}: {response.text}")
                continue

            data = response.json()
            candidate = data.get("candidates", [{}])[0]
            raw_text: str = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

            if not raw_text:
                 continue
                 
            mcqs = _extract_json_array(raw_text)

            if isinstance(mcqs, list) and len(mcqs) > 0:
                return mcqs

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            await asyncio.sleep(1)
            
    return FALLBACK_MCQS

# ─────────────────────────────────────────────────────────────────────────────
# NEW: Daily Mission Planner
# ─────────────────────────────────────────────────────────────────────────────

async def generate_daily_plan(days_remaining: int, pending_topics: list[str], urgent_srs: list[str]) -> list[dict]:
    """Generates optimized daily mission based on user progress."""
    system_instruction = (
        "You are an elite AI study planner. Based on the user's days remaining, "
        "pending syllabus, and urgent decaying memory topics, generate an optimal daily mission. "
        "Output a JSON array of up to 3 objects: { 'task_title', 'reasoning', 'action_type', 'target_topic' }. "
        "'action_type' MUST be exactly one of: 'vault_study', 'arena_practice', 'revision'. "
        "Do not output markdown code blocks. Output pure JSON."
    )
    
    prompt = (
        f"Days Remaining: {days_remaining}\n"
        f"Pending Syllabus: {pending_topics}\n"
        f"Urgent Decaying Memory Topics: {urgent_srs}\n\n"
        "Generate a strictly optimal daily mission matching the exact JSON array schema. "
        "DO NOT use markdown formatting. DO NOT wrap the response in ```json. Output ONLY a raw, valid JSON array."
    )
    
    schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "task_title": {"type": "STRING"},
                "reasoning": {"type": "STRING"},
                "action_type": {"type": "STRING"},
                "target_topic": {"type": "STRING"}
            },
            "required": ["task_title", "reasoning", "action_type", "target_topic"]
        }
    }
    
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }
    
    import asyncio
    import json
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(GEMINI_URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                # --- EXTREME JSON EXTRACTION ---
                raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                
                import re
                # Use Regex to find the first '[' and last ']' and grab everything in between
                match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                
                if match:
                    clean_json_string = match.group(0)
                    try:
                        import json
                        mission_plan = json.loads(clean_json_string)
                        return mission_plan
                    except Exception as json_e:
                        print(f"--- [JSON PARSE FAILED AFTER REGEX] ---")
                        print(f"Regex Extracted: {clean_json_string}")
                        print(f"Error: {str(json_e)}")
                else:
                    print(f"--- [NO JSON ARRAY FOUND IN GEMINI RESPONSE] ---")
                    print(f"Raw Output: {raw_text}")
                    
        except Exception as e:
            print(f"--- [LLM NETWORK/STRUCTURE FAILED] ---")
            print(f"Gemini Raw Text: {response.text if 'response' in locals() else 'No Response'}")
            print(f"Error: {str(e)}")
            import asyncio
            await asyncio.sleep(1)
            
    return [{
        "task_title": "Review Default Topic",
        "reasoning": "AI generated invalid format. Reverting to safe default.",
        "action_type": "vault_study",
        "target_topic": pending_topics[0] if pending_topics else "General Concepts"
    }]

# ─────────────────────────────────────────────────────────────────────────────
# NEW: Adaptive PYQ Generator
# ─────────────────────────────────────────────────────────────────────────────

async def generate_adaptive_pyqs(topic: str, past_mistakes: list[str], exam_track: str) -> list[dict]:
    system_instruction = (
        f"You are an expert examiner for the {exam_track} exam. The student is weak at '{topic}'. "
        f"Specifically, they previously struggled with these concepts/questions: {past_mistakes}. "
        f"Generate exactly 5 new MCQs that test this exact weakness. You MUST format these questions "
        f"to mimic the pattern and difficulty of official Past Year Questions (PYQs) for {exam_track}. "
        f"Output ONLY a JSON array of 5 objects: {{'question', 'options', 'correct_answer', 'explanation'}}."
    )
    
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": "Format the output STRICTLY as a JSON array of 5 MCQ objects."}]}],
        "generationConfig": {
            "temperature": 0.5,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA
        }
    }
    
    import asyncio
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(GEMINI_URL, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                data = response.json()
                raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                
                mcqs = _extract_json_array(raw_text)
                if isinstance(mcqs, list) and len(mcqs) > 0:
                    return mcqs
        except Exception as e:
            logger.warning(f"Adaptive attempt {attempt+1} failed: {e}")
            await asyncio.sleep(1)
            
    return FALLBACK_MCQS