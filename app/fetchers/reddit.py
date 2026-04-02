import asyncio
import httpx
import os

from datetime import datetime, timezone
from typing import Any

REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "unknown-user")

HEADERS = {"User-Agent": "it-news-aggregator/0.1 by {REDDIT_USERNAME}"}
TIMEOUT = 10.0


async def fetch_subreddit(subreddit: str, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch latest posts from a subreddit and return normalized article dicts."""
    url = f"https://www.reddit.com/r/{subreddit}/new.json"

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        resp = await client.get(url, params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()

    return [
        {
            "source": "reddit",
            "source_detail": f"r/{subreddit}",
            "external_id": post["data"]["id"],
            "title": post["data"]["title"],
            "url": f"https://www.reddit.com{post['data']['permalink']}",
            "summary": post["data"].get("selftext") or "", 
            "published_at": datetime.fromtimestamp(
                post["data"]["created_utc"], tz=timezone.utc
            ),
        }
        for post in data["data"]["children"]
    ]
