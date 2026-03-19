import json
import os
import re
import httpx
import logging
from dotenv import load_dotenv
from fastapi import HTTPException

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

# ── System Instruction ───────────────────────────────────────────────────────
SYSTEM_INSTRUCTION = (
    "You are an expert exam question creator for Indian competitive entrance exams (JEE / NEET). "
    "Output ONLY a valid JSON array of exactly 5 objects. "
    "NEVER use unescaped double quotes inside your text strings. "
    "If you need to quote a term inside a question or explanation, use single quotes instead. "
    "Do NOT wrap your response in markdown code fences or backticks. "
    "Do NOT add any text before or after the JSON array. "
    "Ensure the JSON is perfectly formatted and can be parsed by Python's json.loads()."
)

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


def _build_payload(topic: str) -> dict:
    """Construct the full Gemini REST API request payload."""
    return {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Generate 5 MCQs about: {topic}"}],
            }
        ],
        "generationConfig": {
            "temperature":      0.7,
            "maxOutputTokens":  3000,
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
    print(raw_text)          # complete text — no truncation
    print(f"{border}\n")
    raise HTTPException(
        status_code=503,
        detail=f"AI returned malformed JSON: {reason}",
    )


async def generate_mcqs(topic: str) -> list[dict]:
    """
    Calls the Gemini REST API via httpx and returns 5 MCQ dicts.
    Uses a regex-based extractor to survive markdown fences and
    unescaped quotes in the raw model output.
    """
    payload = _build_payload(topic)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                GEMINI_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

        # ── Non-200 response ──────────────────────────────────────────────
        if response.status_code != 200:
            border = "=" * 70
            print(f"\n{border}")
            print(f"🔥  GEMINI REST API FAILED — HTTP {response.status_code}")
            print(f"TOPIC       : {topic}")
            print(f"RAW RESPONSE: {response.text}")
            print(f"{border}\n")
            raise HTTPException(
                status_code=503,
                detail=f"Gemini API HTTP {response.status_code}: {response.text[:300]}",
            )

        # ── Extract nested text ───────────────────────────────────────────
        data = response.json()
        raw_text: str = data["candidates"][0]["content"]["parts"][0]["text"]

        print(f"\n--- RAW GEMINI TEXT for '{topic}' (first 600 chars) ---")
        print(raw_text[:600])
        print("--- END ---\n")

        # ── Bulletproof parse ─────────────────────────────────────────────
        mcqs = _extract_json_array(raw_text)

        if not isinstance(mcqs, list) or len(mcqs) == 0:
            raise HTTPException(
                status_code=503,
                detail=f"Parsed result is not a non-empty list: {type(mcqs).__name__}",
            )

        return mcqs

    except HTTPException:
        raise  # Never double-wrap HTTPExceptions

    except Exception as e:
        border = "#" * 70
        print(f"\n{border}")
        print("🔥  UNEXPECTED ERROR in generate_mcqs")
        print(f"TOPIC : {topic}")
        print(f"TYPE  : {type(e).__name__}")
        print(f"ERROR : {str(e)}")
        print(f"{border}\n")
        raise HTTPException(
            status_code=503,
            detail=f"AI Error: {str(e)}",
        )
