import json
import os
import re
import httpx
import logging
from dotenv import load_dotenv
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ── API Key ───────────────────────────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip("'").strip('"')

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment or .env file.")

# ── Endpoint ──────────────────────────────────────────────────────────────────
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
)

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_INSTRUCTION = (
    "You are a strict but encouraging JEE/NEET tutor. "
    "The student got a question wrong. Your job is to analyse their logic and give targeted feedback. "
    "Compare the user_logic field to the correct_answer field. "
    "Identify the exact mathematical or conceptual misstep in the student's approach. "
    "Do NOT simply reveal the answer — explain WHY their specific approach failed and what the correct mental model is. "
    "Also, produce a highly specific 3-4 word YouTube search query (in English) that targets exactly the sub-concept they are struggling with. "
    "Output ONLY valid JSON with exactly two string keys: 'feedback' and 'youtube_query'. "
    "NEVER use unescaped double quotes inside string values — use single quotes instead. "
    "Do not wrap the JSON in markdown code fences."
)

# ── Response Schema (REST format) ─────────────────────────────────────────────
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "feedback":      {"type": "STRING"},
        "youtube_query": {"type": "STRING"},
    },
    "required": ["feedback", "youtube_query"],
}


def _build_payload(question: str, correct_answer: str, user_logic: str) -> dict:
    user_message = (
        f"Question: {question}\n"
        f"Correct Answer: {correct_answer}\n"
        f"Student's Logic / Attempt: {user_logic}"
    )
    return {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}],
            }
        ],
        "generationConfig": {
            "temperature":      0.4,   # Low temp → more precise, consistent feedback
            "maxOutputTokens":  1024,
            "responseMimeType": "application/json",
            "responseSchema":   RESPONSE_SCHEMA,
        },
    }


def _parse_json_object(raw_text: str) -> dict:
    """
    Extract the first {...} JSON object from raw_text using regex,
    then parse it. Falls back to a direct parse if regex finds nothing.
    """
    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    json_str = match.group(0) if match else raw_text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        border = "!" * 70
        print(f"\n{border}")
        print("🔥  TUTOR JSON PARSE FAILURE")
        print(f"REASON : {e}")
        print(f"RAW TEXT (full):\n{raw_text}")
        print(f"{border}\n")
        raise HTTPException(
            status_code=503,
            detail=f"AI tutor returned malformed JSON: {e}",
        )


async def evaluate_user_logic(
    question: str,
    correct_answer: str,
    user_logic: str,
) -> dict:
    """
    Calls the Gemini REST API to analyse a student's incorrect approach.
    Returns a dict with 'feedback' (str) and 'youtube_query' (str).
    """
    payload = _build_payload(question, correct_answer, user_logic)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                GEMINI_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

        if response.status_code != 200:
            print(f"🔥 GEMINI TUTOR API FAILED — HTTP {response.status_code}\n{response.text}")
            raise HTTPException(
                status_code=503,
                detail=f"Gemini tutor API HTTP {response.status_code}: {response.text[:300]}",
            )

        data = response.json()
        raw_text: str = data["candidates"][0]["content"]["parts"][0]["text"]

        print(f"\n--- RAW TUTOR RESPONSE ---\n{raw_text[:500]}\n--- END ---\n")

        result = _parse_json_object(raw_text)

        # Validate expected keys are present
        if "feedback" not in result or "youtube_query" not in result:
            raise HTTPException(
                status_code=503,
                detail=f"AI tutor response missing required keys: {list(result.keys())}",
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        print(f"\n{'#'*70}")
        print(f"🔥 UNEXPECTED ERROR in evaluate_user_logic")
        print(f"TYPE  : {type(e).__name__}")
        print(f"ERROR : {str(e)}")
        print(f"{'#'*70}\n")
        raise HTTPException(
            status_code=503,
            detail=f"AI Tutor Error: {str(e)}",
        )
