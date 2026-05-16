import asyncio
from datetime import datetime, timedelta
from typing import Optional

from qdrant_client import models
from qdrant_client.http.models import Document

from qdrant_client.http.exceptions import ResponseHandlingException

from ...lib.qdrant import get_qdrant_client, reset_qdrant_client, CATALOG_COLLECTION, CATALOG_EMBED_MODEL
from ...core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


async def _qdrant_query(method_name: str, *args, **kwargs):
    """Call a QdrantClient method by name, retrying once on stale connection."""
    client = get_qdrant_client()
    try:
        return await asyncio.to_thread(getattr(client, method_name), *args, **kwargs)
    except ResponseHandlingException:
        logger.warning("Qdrant connection error, resetting client and retrying")
        await asyncio.sleep(2)
        client = reset_qdrant_client()
        return await asyncio.to_thread(getattr(client, method_name), *args, **kwargs)


def _point_to_dict(point) -> dict:
    payload = point.payload or {}
    score = getattr(point, "score", None)
    return {
        "arxiv_id": payload.get("arxiv_id"),
        "title": payload.get("title"),
        "abstract": payload.get("abstract"),
        "authors": payload.get("authors"),
        "categories": payload.get("categories"),
        "primary_category": payload.get("primary_category"),
        "published_date": payload.get("published_date"),
        "paper_url": payload.get("paper_url"),
        "pdf_url": payload.get("pdf_url"),
        "score": score,
        "final_score": None,
    }


def _exclude(results: list[dict], exclude_ids: set[str]) -> list[dict]:
    if not exclude_ids:
        return results
    return [r for r in results if r.get("arxiv_id") not in exclude_ids]


async def get_similar_papers(
    title: str,
    abstract: str,
    exclude_ids: list[str],
    top_k: int = 20,
) -> list[dict]:
    results = await _qdrant_query(
        "query_points",
        collection_name=CATALOG_COLLECTION,
        query=Document(
            text=f"{title} {abstract}",
            model=CATALOG_EMBED_MODEL,
        ),
        using=CATALOG_EMBED_MODEL,
        limit=top_k + len(exclude_ids),
        with_payload=True,
    )
    items = [_point_to_dict(p) for p in results.points]
    return _exclude(items, set(exclude_ids))[:top_k]


async def get_similar_on_topic(
    title: str,
    abstract: str,
    primary_category: str,
    exclude_ids: list[str],
    top_k: int = 10,
) -> list[dict]:
    results = await _qdrant_query(
        "query_points",
        collection_name=CATALOG_COLLECTION,
        query=Document(
            text=f"{title} {abstract}",
            model=CATALOG_EMBED_MODEL,
        ),
        using=CATALOG_EMBED_MODEL,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="primary_category",
                    match=models.MatchValue(value=primary_category),
                )
            ],
        ),
        limit=top_k + len(exclude_ids),
        with_payload=True,
    )
    items = [_point_to_dict(p) for p in results.points]
    return _exclude(items, set(exclude_ids))[:top_k]


async def get_papers_by_authors(
    authors_str: str,
    exclude_ids: list[str],
    top_k: int = 10,
) -> list[dict]:
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

        scroll_result, _ = await _qdrant_query(
            "scroll",
            collection_name=CATALOG_COLLECTION,
            scroll_filter=scroll_filter,
            limit=top_k + len(seen),
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


async def get_feed_recommendations(
    query_texts: list[str],
    category_filter: list[str],
    exclude_ids: list[str],
    offset: int = 0,
    limit: int = 24,
) -> list[dict]:
    """Aggregate vector search across multiple saved papers, filtered by categories."""
    combined = " ".join(query_texts)[:2000]

    fetch_count = offset + limit + len(exclude_ids)

    category_must = []
    if category_filter:
        category_must.append(
            models.FieldCondition(
                key="primary_category",
                match=models.MatchAny(any=category_filter),
            )
        )

    results = await _qdrant_query(
        "query_points",
        collection_name=CATALOG_COLLECTION,
        query=Document(
            text=combined,
            model=CATALOG_EMBED_MODEL,
        ),
        using=CATALOG_EMBED_MODEL,
        query_filter=models.Filter(must=category_must) if category_must else None,
        limit=fetch_count,
        with_payload=True,
    )

    items = [_point_to_dict(p) for p in results.points]
    items = _exclude(items, set(exclude_ids))
    return items[offset : offset + limit]


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
