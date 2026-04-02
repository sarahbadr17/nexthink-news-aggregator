import asyncio
import logging
from typing import Any

from app.fetchers.reddit import fetch_subreddit
from app.fetchers.sites import fetch_all_sites
from app.classification.classifier import classify_batch
from app.db.repository import ArticleRepository

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60
MAX_LLM_REQUESTS_PER_MINUTE = 3
BATCH_SIZE = 10

repo = ArticleRepository()

def chunked(items: list[Any], size: int) -> list[list[Any]]:
    """Split a list of items into batches of a given size."""
    return [items[i:i + size] for i in range(0, len(items), size)]


async def fetch_and_store_articles() -> int:
    """Fetch from all sources and store only new articles."""
    logger.info("Starting ingestion cycle …")

    reddit_articles, site_articles = await asyncio.gather(
        fetch_subreddit("programming", limit=50),
        fetch_all_sites(limit=40),
    )

    raw_articles = reddit_articles + site_articles
    logger.info("Fetched %d raw articles.", len(raw_articles))

    inserted = 0
    for article in raw_articles:
        article_id = repo.add_new_article(article)
        if article_id is not None:
            inserted += 1

    logger.info("Inserted %d new articles.", inserted)
    return inserted


def classify_pending_articles() -> list[dict[str, Any]]:
    """Classify up to 3 batches of unclassified articles from the DB."""
    max_articles = MAX_LLM_REQUESTS_PER_MINUTE * BATCH_SIZE
    pending_articles = repo.get_pending_articles(limit=max_articles)

    if not pending_articles:
        logger.info("No unclassified articles in backlog.")
        return []

    logger.info("Found %d unclassified articles to process.", len(pending_articles))

    stored_articles: list[dict[str, Any]] = []
    article_batches = chunked(pending_articles, BATCH_SIZE)

    for batch_index, batch in enumerate(article_batches[:MAX_LLM_REQUESTS_PER_MINUTE]):
        try:
            categories = classify_batch(batch)

            for article, category in zip(batch, categories):
                repo.set_article_category(article["id"], category.value)
                article["category"] = category.value
                stored_articles.append(article)

                logger.info(
                    "Classified article '%s' as %s.",
                    article["title"],
                    category.value,
                )

        except Exception:
            logger.exception("Failed to classify batch %d.", batch_index)

    remaining = repo.get_pending_articles(limit=1)
    if remaining:
        logger.info("Some articles remain in backlog for the next polling cycle.")

    return stored_articles


async def fetch_and_classify() -> list[dict[str, Any]]:
    """One full cycle: ingest new articles, then classify a limited backlog."""
    await fetch_and_store_articles()
    return classify_pending_articles()


async def run_polling(interval_seconds: int = POLL_INTERVAL_SECONDS) -> None:
    """Run fetching + backlog classification until no pending articles remain."""
    logger.info("Polling loop started (interval=%ds).", interval_seconds)

    while True:
        try:
            articles = await fetch_and_classify()
            logger.info("Cycle done — %d articles classified.", len(articles))

            pending_articles = repo.get_pending_articles(limit=1)
            if not pending_articles:
                logger.info("No more articles to classify. Stopping loop.")
                break

        except Exception:
            logger.exception("Fetch cycle failed: will retry next interval.")

        await asyncio.sleep(interval_seconds)
