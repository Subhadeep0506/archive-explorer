import re
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..controller.arxiv import (
    search_arxiv,
    feed_topics,
    feed_topic_string,
    create_pdf_thumbnail,
)
from ..controller.catalog_controller import get_feed
from ..controller.smart_feed_controller import get_smart_feed, search_catalog_papers
from ..controller.recommendation_controller import get_recommendations_by_metadata
from ..schema.arxiv import ArxivEntry, ThumbnailRequest, ThumbnailResponse
from ..schema.paper import RecommendationRequest, RecommendationsResponse
from ..lib.auth import get_current_user

ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")

router = APIRouter()


@router.get(
    "/search",
    response_model=List[ArxivEntry],
)
async def search(
    search_query: str,
    start: int = 0,
    max_results: int = 10,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    _: int = Depends(get_current_user),
):
    """Search arXiv by query (uses `all:` semantics)."""
    return await search_arxiv(
        search_query=search_query,
        start=start,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/feed", response_model=List[ArxivEntry])
async def feed(
    topics: List[str] = Query(..., description="List of topics, OR-combined"),
    start: int = 0,
    max_results: int = 10,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    _: int = Depends(get_current_user),
):
    """Fetch arXiv feed by topics from the live ArXiv API (fallback/search use)."""
    return await feed_topics(
        topics=topics,
        start=start,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/feed/string", response_model=List[ArxivEntry])
async def feed_string(
    topics_csv: str,
    start: int = 0,
    max_results: int = 10,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    _: int = Depends(get_current_user),
):
    """Fetch arXiv feed by a comma-separated topic string."""
    return await feed_topic_string(
        topics_csv=topics_csv,
        start=start,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/catalog/feed", response_model=List[ArxivEntry])
async def catalog_feed(
    topics: List[str] = Query(..., description="List of primary categories to filter by"),
    start: int = 0,
    limit: int = 20,
    _: int = Depends(get_current_user),
):
    """Fetch papers from the local ArXiv catalog (PostgreSQL-backed) by primary category."""
    return await get_feed(topics=topics, start=start, limit=limit)


@router.get("/catalog/search", response_model=List[ArxivEntry])
async def catalog_search(
    q: str = Query(..., description="Free-text search query"),
    start: int = 0,
    max_results: int = 20,
    _: int = Depends(get_current_user),
):
    """Search the local Qdrant catalog by semantic similarity."""
    return await search_catalog_papers(query=q, start=start, limit=max_results)


@router.get("/smart-feed", response_model=List[ArxivEntry])
async def smart_feed(
    topics: List[str] = Query(..., description="List of primary categories to filter by"),
    start: int = 0,
    limit: int = 24,
    user_id: int = Depends(get_current_user),
):
    """Smart feed: recommends papers based on saved papers if available, otherwise catalog feed."""
    return await get_smart_feed(
        user_id=user_id, topics=topics, start=start, limit=limit
    )


@router.get("/pdf/{arxiv_id}")
async def proxy_pdf(
    arxiv_id: str,
    token: Optional[str] = Query(None, description="JWT access token (for PDF viewer which cannot set headers)"),
):
    """Stream an ArXiv PDF through the backend to avoid CORS issues.

    Accepts auth via query param because PDF viewers load URLs directly
    and cannot set Authorization headers.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    from jose import jwt, JWTError
    import os
    from sqlalchemy import select, desc
    from ..database.db import session_pool
    from ..model.login_session import LoginSession

    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=[os.getenv("JWT_ALGORITHM")],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with session_pool() as session:
        result = await session.execute(
            select(LoginSession)
            .filter_by(user_id=int(user_id), access_token=token, is_active=True)
            .order_by(desc(LoginSession.created_at))
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=401, detail="Token revoked or inactive")

    if not ARXIV_ID_RE.match(arxiv_id):
        raise HTTPException(status_code=400, detail="Invalid arXiv ID")

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        resp = await client.get(pdf_url)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch PDF from arXiv")

    return StreamingResponse(
        iter([resp.content]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{arxiv_id}.pdf"',
            "Cache-Control": "public, max-age=86400",
        },
    )


@router.post("/recommendations", response_model=RecommendationsResponse)
async def recommendations_by_metadata(
    payload: RecommendationRequest,
    limit: int = Query(default=10, ge=1, le=50),
    user_id: int = Depends(get_current_user),
):
    """Get hybrid recommendations from paper metadata (no save required)."""
    return await get_recommendations_by_metadata(
        req=payload, user_id=user_id, limit=limit
    )


@router.get("/categories")
async def get_categories():
    """Return the list of valid arXiv categories with labels."""
    from ..lib.categories import VALID_ARXIV_CATEGORIES
    return VALID_ARXIV_CATEGORIES


@router.post("/thumbnail", response_model=ThumbnailResponse)
async def generate_thumbnail(
    payload: ThumbnailRequest,
    user_id: int = Depends(get_current_user),
):
    """Generate and upload first-page PDF thumbnail, returning its public URL."""
    return await create_pdf_thumbnail(
        user_id=user_id,
        pdf_url=payload.pdf_url,
        target_width=payload.target_width or 400,
        folder=payload.folder or "thumbnails",
    )
