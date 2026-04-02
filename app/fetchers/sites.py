import asyncio
import feedparser
import httpx
import logging

from datetime import datetime, timezone
from typing import Any

TIMEOUT = 10.0
HEADERS = {"User-Agent": "it-news-aggregator/0.1"}
logger = logging.getLogger(__name__)

SOURCES = {
    "ars_technica": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "techcrunch": "https://techcrunch.com/feed/",
}


async def fetch_rss(
    client: httpx.AsyncClient,
    source_name: str,
    feed_url: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    resp = await client.get(feed_url)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)

    articles = []
    for entry in feed.entries[:limit]:
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        articles.append(
            {
                "source": source_name,
                "source_detail": feed_url,
                "external_id": getattr(entry, "id", getattr(entry, "link", None)),
                "title": getattr(entry, "title", ""),
                "url": getattr(entry, "link", ""),
                "summary": getattr(entry, "summary", None),
                "published_at": published_at,
            }
        )

    return articles


async def fetch_all_sites(limit: int = 20) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        tasks = [
            fetch_rss(client, source_name, feed_url, limit)
            for source_name, feed_url in SOURCES.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    articles = []
    for source_name, result in zip(SOURCES.keys(), results):
        if isinstance(result, Exception):
            logger.error("Failed to fetch %s: %s", source_name, result)
        else:
            logger.info("Fetched %d articles from %s", len(result), source_name)
            articles.extend(result)

    return articles
