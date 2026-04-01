# IT News Aggregator

A small real-time IT news aggregation system built for the Nexthink Software Engineer take-home assignment. It fetches IT news from Reddit and RSS feeds, classifies articles into predefined categories with an LLM, stores them in a local database, and exposes a simple API for search and retrieval.

## Setup

### 1. Create a Python environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root and add:

```env
OPENAI_API_KEY=your_openai_api_key
REDDIT_USERNAME=your_reddit_username
```

## Run the project

Start the ingestion/classification pipeline with:

```bash
python3 -m app.main
```

## API

The API supports the two required operations from the assignment: searching for news articles by user prompt and/or category, and retrieving a specific article. 

### Search articles

```http
GET /articles?q=security&category=Cybersecurity
```

Example query parameters:

- `q`: free-text search on article title/summary
- `category`: optional category filter
- `limit`: maximum number of results returned

### Retrieve one article

```http
GET /articles/{article_id}
```

## Tests

Run all tests with:

```bash
pytest tests/
```

## Repository structure

```text
app/
├── api/
│   └── api.py                 # FastAPI routes
├── classification/
│   ├── categories.py          # Category enum
│   └── classifier.py          # Single and batch LLM classification
├── db/
│   └── repository.py          # SQLite repository layer
├── fetchers/
│   ├── pipeline.py            # Ingestion + classification loop
│   ├── reddit.py              # Reddit fetcher
│   └── sites.py               # RSS/news-site fetcher
├── main.py                    # Application entry point

tests/
├── test_api.py                # Basic API tests
└── test_classifier.py         # Basic classifier tests               
```

## Notes

- The classifier currently relies on article title and summary text rather than full article body content
- The implementation focuses on clean modularity and core functionality over production completeness
