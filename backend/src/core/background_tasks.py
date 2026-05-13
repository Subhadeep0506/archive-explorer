import asyncio

from sqlalchemy import select

from ..database.db import session_pool
from ..model.paper import Paper
from ..core.keyword_engine.extractor import extract_keywords, keywords_to_string
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


async def index_paper_background(paper_id: int, title: str, abstract: str) -> None:
    """FastAPI BackgroundTask: extract keywords via SciBERT ONNX and store in Paper.keywords."""
    try:
        keywords = await asyncio.to_thread(extract_keywords, title, abstract, 10)
        keywords_str = keywords_to_string(keywords)

        async with session_pool() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id)
            )
            paper = result.scalar_one_or_none()
            if paper:
                paper.keywords = keywords_str
                await session.commit()
                logger.info(f"Keywords extracted for paper_id={paper_id}: {keywords_str[:100]}")
    except Exception as e:
        logger.warning(f"Keyword extraction failed for paper_id={paper_id}: {e}")
