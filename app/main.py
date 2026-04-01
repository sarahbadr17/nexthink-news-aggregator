import asyncio
import logging

logger = logging.getLogger(__name__)

from app.fetchers.pipeline import run_polling

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    asyncio.run(run_polling())
