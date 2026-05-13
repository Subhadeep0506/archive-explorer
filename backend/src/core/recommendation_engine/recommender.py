import asyncio
from datetime import datetime, timedelta
from typing import Optional

from qdrant_client import models
from qdrant_client.http.models import Document

from ...lib.qdrant import get_qdrant_client, CATALOG_COLLECTION, CATALOG_EMBED_MODEL
from ...core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


def _point_to_dict(point) -> dict:
    payload = point.payload or {}
    score = getattr(point, "score", None)
    return {
        "arxiv_id": payload.get("arxiv_id"),
        "title": payload.get("title"),
        "authors": payload.get("authors"),
        "categories": payload.get("categories"),
        "primary_category": payload.get("primary_category"),
        "published_date": payload.get("published_date"),
        "paper_url": payload.get("paper_url"),
        "pdf_url": payload.get("pdf_url"),
        "score": score,
        "final_score": None,
    }


async def get_similar_papers(
    title: str,
    abstract: str,
    exclude_ids: list[str],
    top_k: int = 20,
) -> list[dict]:
    client = get_qdrant_client()
    query_filter = None
    if exclude_ids:
        query_filter = models.Filter(
            must_not=[
                models.FieldCondition(
                    key="arxiv_id",
                    match=models.MatchAny(any=exclude_ids),
                )
            ]
        )

    results = await asyncio.to_thread(
        client.query_points,
        collection_name=CATALOG_COLLECTION,
        query=Document(
            text=f"{title} {abstract}",
            model=CATALOG_EMBED_MODEL,
        ),
        using=CATALOG_EMBED_MODEL,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )
    return [_point_to_dict(p) for p in results.points]


async def get_similar_on_topic(
    title: str,
    abstract: str,
    primary_category: str,
    exclude_ids: list[str],
    top_k: int = 10,
) -> list[dict]:
    client = get_qdrant_client()
    must_conditions = [
        models.FieldCondition(
            key="primary_category",
            match=models.MatchValue(value=primary_category),
        )
    ]
    must_not_conditions = []
    if exclude_ids:
        must_not_conditions.append(
            models.FieldCondition(
                key="arxiv_id",
                match=models.MatchAny(any=exclude_ids),
            )
        )

    results = await asyncio.to_thread(
        client.query_points,
        collection_name=CATALOG_COLLECTION,
        query=Document(
            text=f"{title} {abstract}",
            model=CATALOG_EMBED_MODEL,
        ),
        using=CATALOG_EMBED_MODEL,
        query_filter=models.Filter(
            must=must_conditions,
            must_not=must_not_conditions if must_not_conditions else None,
        ),
        limit=top_k,
        with_payload=True,
    )
    return [_point_to_dict(p) for p in results.points]


async def get_papers_by_authors(
    authors_str: str,
    exclude_ids: list[str],
    top_k: int = 10,
) -> list[dict]:
    client = get_qdrant_client()
    author_list = [a.strip() for a in authors_str.split(";") if a.strip()][:5]

    results = []
    seen = set(exclude_ids)

    for author in author_list:
        scroll_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="authors",
                    match=models.MatchText(text=author),
                )
            ]
        )
        if exclude_ids:
            scroll_filter.must_not = [
                models.FieldCondition(
                    key="arxiv_id",
                    match=models.MatchAny(any=list(seen)),
                )
            ]

        scroll_result, _ = await asyncio.to_thread(
            client.scroll,
            collection_name=CATALOG_COLLECTION,
            scroll_filter=scroll_filter,
            limit=top_k,
            with_payload=True,
        )

        for p in scroll_result:
            arxiv_id = p.payload.get("arxiv_id")
            if arxiv_id and arxiv_id not in seen:
                seen.add(arxiv_id)
                results.append(_point_to_dict(p))

        if len(results) >= top_k:
            break

    return results[:top_k]


def rerank_results(
    candidates: list[dict],
    user_saved_categories: list[str],
) -> list[dict]:
    """Re-rank recommendation candidates by similarity, category affinity, and recency."""
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    six_months_ago = now - timedelta(days=180)

    for candidate in candidates:
        similarity = candidate.get("score") or 0.0

        category_affinity = 0.0
        if candidate.get("primary_category") in user_saved_categories:
            category_affinity = 1.0

        recency = 0.0
        pub_date_str = candidate.get("published_date")
        if pub_date_str:
            try:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                if pub_date >= thirty_days_ago:
                    recency = 1.0
                elif pub_date >= six_months_ago:
                    recency = 0.5
            except ValueError:
                pass

        candidate["final_score"] = (
            0.60 * similarity
            + 0.15 * category_affinity
            + 0.15 * recency
            + 0.10 * 0.5
        )

    candidates.sort(key=lambda c: c.get("final_score", 0), reverse=True)
    return candidates
