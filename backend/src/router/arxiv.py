from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from ..controller.arxiv import (
    search_arxiv,
    feed_topics,
    feed_topic_string,
    create_pdf_thumbnail,
)
from ..schema.arxiv import ArxivEntry, ThumbnailRequest, ThumbnailResponse
from ..lib.auth import get_current_user


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
    include_thumbnails: bool = False,
    max_thumbnail_concurrency: int = 3,
    thumbnail_timeout_sec: int = 20,
    user_id: int = Depends(get_current_user),
):
    """Fetch arXiv feed by topics (OR-combined)."""
    return await feed_topics(
        topics=topics,
        start=start,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order,
        include_thumbnails=include_thumbnails,
        max_thumbnail_concurrency=max_thumbnail_concurrency,
        thumbnail_timeout_sec=thumbnail_timeout_sec,
        user_id=user_id,
    )


@router.get("/feed/string", response_model=List[ArxivEntry])
async def feed_string(
    topics_csv: str,
    start: int = 0,
    max_results: int = 10,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    include_thumbnails: bool = False,
    max_thumbnail_concurrency: int = 3,
    thumbnail_timeout_sec: int = 20,
    user_id: int = Depends(get_current_user),
):
    """Fetch arXiv feed by a comma-separated topic string."""
    return await feed_topic_string(
        topics_csv=topics_csv,
        start=start,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order,
        include_thumbnails=include_thumbnails,
        max_thumbnail_concurrency=max_thumbnail_concurrency,
        thumbnail_timeout_sec=thumbnail_timeout_sec,
        user_id=user_id,
    )


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
