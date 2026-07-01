import asyncio

from fastapi import HTTPException
from sqlalchemy import select

from ..database.db import session_pool
from ..model.paper import Paper
from ..model.arxiv_catalog import ArxivCatalog
from ..schema.paper import RecommendationItem, RecommendationRequest, RecommendationsResponse
from ..core.recommendation_engine.recommender import (
    get_similar_papers,
    get_similar_on_topic,
    get_papers_by_authors,
    rerank_results,
)
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


async def get_recommendations_by_metadata(
    req: RecommendationRequest,
    user_id: int,
    limit: int = 10,
) -> RecommendationsResponse:
    async with session_pool() as session:
        all_papers_result = await session.execute(
            select(Paper.arxiv_id).where(
                Paper.user_id == user_id, Paper.arxiv_id.isnot(None)
            )
        )
        saved_arxiv_ids = [row[0] for row in all_papers_result.all()]

        user_saved_categories: list[str] = []
        if saved_arxiv_ids:
            catalog_result = await session.execute(
                select(ArxivCatalog.primary_category)
                .where(ArxivCatalog.arxiv_id.in_(saved_arxiv_ids))
                .distinct()
            )
            user_saved_categories = [
                row[0] for row in catalog_result.all() if row[0]
            ]

    exclude_ids = saved_arxiv_ids
    if req.arxiv_id:
        exclude_ids = list(set(saved_arxiv_ids + [req.arxiv_id]))

    primary_category = req.primary_category

    async def _empty_list() -> list:
        return []

    similar_task = get_similar_papers(
        req.title, req.abstract, exclude_ids, top_k=limit * 2
    )
    on_topic_task = (
        get_similar_on_topic(
            req.title, req.abstract, primary_category, exclude_ids, top_k=limit
        )
        if primary_category
        else _empty_list()
    )
    by_authors_task = get_papers_by_authors(
        req.authors, exclude_ids, top_k=limit
    )

    similar, on_topic, by_authors = await asyncio.gather(
        similar_task, on_topic_task, by_authors_task
    )

    reranked_similar = rerank_results(similar, user_saved_categories)[:limit]

    return RecommendationsResponse(
        similar_papers=[RecommendationItem(**p) for p in reranked_similar],
        on_this_topic=[RecommendationItem(**p) for p in on_topic[:limit]],
        from_these_authors=[RecommendationItem(**p) for p in by_authors[:limit]],
    )


async def get_recommendations_for_paper(
    paper_id: int,
    user_id: int,
    limit: int = 10,
) -> RecommendationsResponse:
    async with session_pool() as session:
        result = await session.execute(
            select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
        )
        paper = result.scalar_one_or_none()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        all_papers_result = await session.execute(
            select(Paper.arxiv_id).where(
                Paper.user_id == user_id, Paper.arxiv_id.isnot(None)
            )
        )
        saved_arxiv_ids = [row[0] for row in all_papers_result.all()]

        # Cross-reference with catalog for category affinity
        user_saved_categories: list[str] = []
        if saved_arxiv_ids:
            catalog_result = await session.execute(
                select(ArxivCatalog.primary_category)
                .where(ArxivCatalog.arxiv_id.in_(saved_arxiv_ids))
                .distinct()
            )
            user_saved_categories = [
                row[0] for row in catalog_result.all() if row[0]
            ]

        # Determine primary_category for on-topic query
        primary_category = None
        if paper.arxiv_id:
            cat_result = await session.execute(
                select(ArxivCatalog.primary_category).where(
                    ArxivCatalog.arxiv_id == paper.arxiv_id
                )
            )
            row = cat_result.first()
            if row:
                primary_category = row[0]

        # Fall back to first topic from Paper.topics
        if not primary_category and paper.topics:
            primary_category = paper.topics.split()[0] if paper.topics else None

    async def _empty_list() -> list:
        return []

    # Run all three recommendation queries in parallel
    similar_task = get_similar_papers(
        paper.title, paper.abstract, saved_arxiv_ids, top_k=limit * 2
    )
    on_topic_task = (
        get_similar_on_topic(
            paper.title, paper.abstract, primary_category, saved_arxiv_ids, top_k=limit
        )
        if primary_category
        else _empty_list()
    )
    by_authors_task = get_papers_by_authors(
        paper.authors, saved_arxiv_ids, top_k=limit
    )

    similar, on_topic, by_authors = await asyncio.gather(
        similar_task, on_topic_task, by_authors_task
    )

    reranked_similar = rerank_results(similar, user_saved_categories)[:limit]

    return RecommendationsResponse(
        similar_papers=[RecommendationItem(**p) for p in reranked_similar],
        on_this_topic=[RecommendationItem(**p) for p in on_topic[:limit]],
        from_these_authors=[RecommendationItem(**p) for p in by_authors[:limit]],
    )
