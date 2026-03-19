import os
import httpx
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ── API Key ───────────────────────────────────────────────────────────────────
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip().strip("'").strip('"')

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


async def get_youtube_videos(query: str, max_results: int = 2) -> list[str]:
    """
    Searches YouTube Data API v3 for videos matching the query.
    Returns a list of videoId strings.
    Returns an empty list [] silently if the API fails, quota is exceeded,
    or the key is missing — so the main endpoint never crashes due to YouTube.
    """
    if not YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY is not set. Skipping YouTube search.")
        return []

    params = {
        "part":       "snippet",
        "q":          query,
        "type":       "video",
        "key":        YOUTUBE_API_KEY,
        "maxResults": max_results,
        # Prefer educational content
        "relevanceLanguage": "en",
        "safeSearch":        "strict",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(YOUTUBE_SEARCH_URL, params=params)

        if response.status_code != 200:
            logger.error(
                f"YouTube API failed — HTTP {response.status_code}: {response.text[:200]}"
            )
            return []

        data = response.json()
        items = data.get("items", [])

        video_ids = [
            item["id"]["videoId"]
            for item in items
            if item.get("id", {}).get("kind") == "youtube#video"
        ]

        logger.info(f"YouTube search '{query}' → {video_ids}")
        return video_ids

    except Exception as e:
        # Graceful degradation: YouTube failure NEVER crashes the app
        logger.error(f"YouTube service error for query '{query}': {type(e).__name__}: {e}")
        return []
