from fastapi.testclient import TestClient
import app.api.api as api_module


class FakeRepository:
    def __init__(self):
        self.articles = [
            {
                "id": 1,
                "title": "New AI chip released",
                "source": "ars_technica",
                "url": "https://example.com/ai-chip",
                "published_at": "2026-04-01T10:00:00Z",
                "fetched_at": "2026-04-01T10:05:00Z",
                "category": "Hardware & Devices",
                "summary": "A new AI accelerator was announced.",
            },
            {
                "id": 2,
                "title": "Major security breach reported",
                "source": "techcrunch",
                "url": "https://example.com/security-breach",
                "published_at": "2026-04-01T11:00:00Z",
                "fetched_at": "2026-04-01T11:05:00Z",
                "category": "Cybersecurity",
                "summary": "A large cloud provider disclosed a breach.",
            },
        ]

    def query_articles(self, query=None, category=None, limit=20):
        results = self.articles

        if query:
            q = query.lower()
            results = [
                a for a in results
                if q in a["title"].lower() or q in (a.get("summary") or "").lower()
            ]

        if category:
            results = [a for a in results if a["category"] == category]

        return results[:limit]

    def get_article_by_id(self, article_id: int):
        for article in self.articles:
            if article["id"] == article_id:
                return article
        return None


def make_client():
    api_module.repo = FakeRepository()
    return TestClient(api_module.app)


def test_search_articles_by_query():
    client = make_client()

    response = client.get("/articles", params={"q": "security"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 2
    assert data[0]["category"] == "Cybersecurity"


def test_search_articles_by_category():
    client = make_client()

    response = client.get("/articles", params={"category": "Hardware & Devices"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["title"] == "New AI chip released"


def test_get_article_by_id_found():
    client = make_client()

    response = client.get("/articles/1")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "New AI chip released"


def test_get_article_by_id_not_found():
    client = make_client()

    response = client.get("/articles/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"