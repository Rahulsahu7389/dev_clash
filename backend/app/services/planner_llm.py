import os
import json
import httpx
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip("'").strip('"')

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.5-flash:generateContent?key={API_KEY}"
)

# Response schema to enforce JSON structure
PLANNER_SCHEMA = {
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

async def generate_daily_plan(days_remaining: int, pending_topics: list, srs_due: list, weak_topics: list) -> list:
    if not API_KEY:
        logger.error("GEMINI_API_KEY not found for planner_llm")
        return []
        
    system_instruction = (
        "You are an elite, strict AI study mentor. Based on the user's days remaining, "
        "pending syllabus topics, spaced repetition dues, and weak areas, generate a highly "
        "optimized daily study plan. Output ONLY a valid JSON array of 3 to 4 objects. "
        "Each object must have: 'task_title' (string), 'reasoning' (string explaining why "
        "this is prioritized today), 'action_type' (string: strictly one of 'vault_study', "
        "'arena_practice', or 'proctor_test'), and 'target_topic' (string)."
    )
    
    prompt = (
        f"Days Remaining until Exam: {days_remaining}\n"
        f"Pending Syllabus Topics: {pending_topics}\n"
        f"Topics Due for Spaced Repetition (SRS): {srs_due}\n"
        f"Frequent Weak Topics (from mistakes): {weak_topics}\n\n"
        "Generate a 3-4 task study plan for today. IMPORTANT: Ensure the output is valid JSON and perfectly matches the schema."
    )
    
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
            "responseSchema": PLANNER_SCHEMA,
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GEMINI_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                
                import re
                match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(0)
                    
                plan = json.loads(raw_text)
                if isinstance(plan, list):
                    return plan
            else:
                logger.error(f"Planner LLM failed with {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Error calling Planner LLM: {str(e)}")
        
    # Fallback Data in case the LLM is down or timeouts
    return [
        {
            "task_title": "Review Pending Topics",
            "reasoning": "Fallback task generated because AI system is currently evaluating other data.",
            "action_type": "vault_study",
            "target_topic": pending_topics[0] if pending_topics else "General Syllabus"
        }
    ]
