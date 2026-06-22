from sqlalchemy import select, desc

from ..database.db import session_pool
from ..model.paper import Paper
from ..model.arxiv_catalog import ArxivCatalog
from ..schema.arxiv import ArxivEntry
from ..controller.catalog_controller import get_feed
from ..core.recommendation_engine.recommender import (
    get_feed_recommendations,
    rerank_results,
    search_catalog,
)
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()

MAX_SEED_PAPERS = 5


def _qdrant_results_to_entries(items: list[dict]) -> list[ArxivEntry]:
    entries: list[ArxivEntry] = []
    for item in items:
        authors_str = item.get("authors") or ""
        authors = [a.strip() for a in authors_str.split(";") if a.strip()] if authors_str else []
        categories_str = item.get("categories") or ""
        categories = categories_str.split() if categories_str else []

        entries.append(
            ArxivEntry(
                id=str(item.get("arxiv_id") or ""),
                arxiv_id=item.get("arxiv_id"),
                title=item.get("title") or "Untitled",
                abstract=item.get("abstract") or "",
                authors=authors,
                categories=categories,
                primary_category=item.get("primary_category"),
                published=item.get("published_date"),
                updated=None,
                pdf_url=item.get("pdf_url"),
                paper_url=item.get("paper_url"),
            )
        )
    return entries


async def search_catalog_papers(
    query: str,
    start: int = 0,
    limit: int = 20,
) -> list[ArxivEntry]:
    try:
        results = await search_catalog(query=query, offset=start, limit=limit)
        return _qdrant_results_to_entries(results)
    except Exception as exc:
        logger.error("Catalog search failed: %s", exc)
        raise


async def get_smart_feed(
    user_id: int,
    topics: list[str],
    start: int = 0,
    limit: int = 24,
) -> list[ArxivEntry]:
    async with session_pool() as session:
        saved_result = await session.execute(
            select(Paper)
            .where(Paper.user_id == user_id, Paper.arxiv_id.isnot(None))
            .order_by(desc(Paper.created_at))
        )
        saved_papers = saved_result.scalars().all()

    if not saved_papers:
        return await get_feed(topics=topics, start=start, limit=limit)

    saved_arxiv_ids = [p.arxiv_id for p in saved_papers if p.arxiv_id]

    seed_papers = saved_papers[:MAX_SEED_PAPERS]
    query_texts = [
        f"{p.title} {(p.abstract or '')[:200]}" for p in seed_papers
    ]

    async with session_pool() as session:
        cat_result = await session.execute(
            select(ArxivCatalog.primary_category)
            .where(ArxivCatalog.arxiv_id.in_(saved_arxiv_ids))
            .distinct()
        )
        user_saved_categories = [row[0] for row in cat_result.all() if row[0]]

    try:
        results = await get_feed_recommendations(
            query_texts=query_texts,
            category_filter=topics,
            exclude_ids=saved_arxiv_ids,
            offset=start,
            limit=limit,
        )
        reranked = rerank_results(results, user_saved_categories)[:limit]
        return _qdrant_results_to_entries(reranked)
    except Exception as exc:
        logger.warning("Qdrant unavailable, falling back to catalog feed: %s", exc)
        return await get_feed(topics=topics, start=start, limit=limit)
