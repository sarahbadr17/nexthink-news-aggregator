from fastapi import FastAPI, HTTPException, Query
from app.db.repository import ArticleRepository

app = FastAPI(title="IT Newsfeed API")
repo = ArticleRepository()


@app.get("/articles")
def search_articles(
    q: str | None = Query(
        default=None,
        description="Free-text query on title and summary.",
    ),
    category: str | None = Query(
        default=None,
        description="Optional category filter (e.g. 'Cybersecurity').",
    ),
    limit: int = Query(
        default=20,
        le=100,
        description="Maximum number of articles to return.",
    ),
):
    """
    Search classified news articles by free-text query and/or category.
    """
    return repo.query_articles(query=q, category=category, limit=limit)


@app.get("/articles/{article_id}")
def get_article(article_id: int):
    """
    Retrieve a single article by its numeric ID.
    """
    article = repo.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article