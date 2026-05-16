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


async def backfill_missing_keywords() -> int:
    """One-time startup task: extract keywords for saved papers that have none."""
    async with session_pool() as session:
        result = await session.execute(
            select(Paper)
            .where(Paper.keywords.is_(None), Paper.title.isnot(None), Paper.abstract.isnot(None))
        )
        papers = result.scalars().all()

    if not papers:
        logger.info("No papers need keyword backfill")
        return 0

    logger.info(f"Backfilling keywords for {len(papers)} papers")
    count = 0
    for p in papers:
        try:
            keywords = await asyncio.to_thread(extract_keywords, p.title, p.abstract, 10)
            keywords_str = keywords_to_string(keywords)
            async with session_pool() as session:
                result = await session.execute(select(Paper).where(Paper.id == p.id))
                paper = result.scalar_one_or_none()
                if paper:
                    paper.keywords = keywords_str
                    await session.commit()
                    count += 1
        except Exception as e:
            logger.warning(f"Keyword backfill failed for paper_id={p.id}: {e}")

    logger.info(f"Keyword backfill complete: {count}/{len(papers)} papers updated")
    return count
