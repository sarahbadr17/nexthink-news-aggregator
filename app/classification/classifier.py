import json
import os
import logging

from dotenv import load_dotenv
from openai import OpenAI
from app.classification.categories import ArticleCategory

logger = logging.getLogger(__name__)

CATEGORIES = [category.value for category in ArticleCategory]

#Load Open AI Client
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)


#Prompts 
SYSTEM_PROMPT = f"""
    You classify IT news articles.

    You must assign each article to exactly one category from this list:
    {", ".join(CATEGORIES)}
    Rules
    1. Reply with the category label ONLY: no explanation, no punctuation.
    2. The reply must be one of the listed labels verbatim.
    3. When in doubt, reply: Other
"""

SYSTEM_BATCH_PROMPT = f"""
    You classify IT news articles.  
    You must assign each article to exactly one category from this list:
        {", ".join(CATEGORIES)}
    Rules:
    1. Return ONLY valid JSON array with no markdown, explanations, or extra keys.
    2. Each array item must be an object with exactly these keys:
    - "id": the same id provided in the input
    - "category": one category label from the allowed list
    3. The category value must match one of the allowed labels verbatim.
    4. Assign exactly one category per input article.
    5. If an article is ambiguous or lacks enough detail, use "Other".
"""

def user_prompt(title: str, summary: str) -> list[dict]:
    """Build a structured prompt for the LLM."""
    article_snippet = (summary or "")[:2000]   
    user_msg = (
        f"Classify this article.\n\n"
        f"Title: {title}\n\n"
        f"Summary: {article_snippet}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    
    ]

def batch_user_prompt(articles: list[dict[str, str]]) -> list[dict[str, str]]:
    """Build a structured prompt for batch classification of multiple articles."""
    normalized_articles = []

    for idx, article in enumerate(articles):
        #Truncate text
        text = (
            article.get("summary")
            or ""
        )[:800]

        normalized_articles.append(
            {
                "id": idx,
                "title": article.get("title", ""),
                "summary": text,
            }
        )

    #Build a single prompt with the list of articles as JSON in the user message
    return [
        {"role": "system", "content": SYSTEM_BATCH_PROMPT},
        {
            "role": "user",
            "content": json.dumps(normalized_articles, ensure_ascii=False),
        },
    ]


#Map LLM string to category
def map_to_category(raw: str) -> ArticleCategory:
    """Map raw LLM output to one of the predefined categories, with normalization."""
    normalized = raw.strip().lower()
    for category in CATEGORIES:
        if normalized == category.lower():
            return ArticleCategory(category)
    return ArticleCategory.OTHER

#Classification functions
def classify(title: str, summary: str) -> ArticleCategory:
    """Classify an article into one of the predefined categories using the LLM."""
    response = client.responses.create(
        model="gpt-5-nano",
        input=user_prompt(title, summary),
    )

    raw_category = response.output_text.strip()
    logger.debug("LLM raw output for article %r: %r", title[:60], raw_category)
    return map_to_category(raw_category)

def classify_batch(articles: list[dict[str, str]]) -> list[ArticleCategory]:
    """Classify a batch of articles, returning a list of categories in the same order."""
    
    #Send the batch prompt to the LLM and get the response
    response = client.responses.create(
        model="gpt-5-nano",
        input=batch_user_prompt(articles),
    )

    raw_category = response.output_text.strip()
    logger.debug("LLM raw output for batch classification: %r", raw_category)

    #Parse the JSON output
    try:
        parsed = json.loads(raw_category)
    except json.JSONDecodeError:
        logger.exception("Failed to parse batch classification JSON.")
        return [ArticleCategory.OTHER for _ in articles]
    
    #Build a mapping of article ID to category from the parsed output
    by_id: dict[int, ArticleCategory] = {}
    for item in parsed:
        try:
            article_id = int(item["id"])
            category = map_to_category(item["category"])
            by_id[article_id] = category
        except Exception:
            logger.exception("Invalid item in batch classification output: %r", item)

    #Return list of categories 
    return [by_id.get(i, ArticleCategory.OTHER) for i in range(len(articles))]
