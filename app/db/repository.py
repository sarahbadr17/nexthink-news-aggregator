import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("data/articles.db")


class ArticleRepository:
    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _normalize_datetime(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    published_at TEXT,
                    fetched_at TEXT NOT NULL,
                    category TEXT,
                    summary TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_category
                ON articles(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_published_at
                ON articles(published_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_title
                ON articles(title)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_url
                ON articles(url)
            """)

    def add_new_article(self, article: dict[str, Any]) -> Optional[int]:
        fetched_at = datetime.now(timezone.utc).isoformat()
        published_at = self._normalize_datetime(article.get("published_at"))

        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO articles (
                    title, source, url, published_at, fetched_at, category, summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                article["title"],
                article["source"],
                article["url"],
                published_at,
                fetched_at,
                None,
                article.get("summary"),
            ))

            if cursor.lastrowid:
                return int(cursor.lastrowid)
            return None

    def article_exists(self, url: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM articles WHERE url = ? LIMIT 1",
                (url,),
            ).fetchone()
            return row is not None

    def get_pending_articles(self, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch articles that have not yet been categorized, ordered by fetched_at ascending."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT id, title, source, url, published_at, fetched_at, category, summary
                FROM articles
                WHERE category IS NULL
                ORDER BY fetched_at ASC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def set_article_category(self, article_id: int, category: str) -> None:
        with self._connect() as conn:
            conn.execute("""
                UPDATE articles
                SET category = ?
                WHERE id = ?
            """, (category, article_id))

    def query_articles(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT id, title, source, url, published_at, fetched_at, category, summary
            FROM articles
            WHERE category IS NOT NULL
        """
        params: list[Any] = []

        if query:
            sql += " AND (title LIKE ? OR summary LIKE ?)"
            like_query = f"%{query}%"
            params.extend([like_query, like_query])

        if category:
            sql += " AND category = ?"
            params.append(category)

        sql += " ORDER BY COALESCE(published_at, fetched_at) DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def get_article_by_id(self, article_id: int) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT id, title, source, url, published_at, fetched_at, category, summary
                FROM articles
                WHERE id = ?
            """, (article_id,)).fetchone()

            return dict(row) if row else None