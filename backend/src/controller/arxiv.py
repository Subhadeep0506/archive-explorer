from typing import List, Optional
from fastapi import HTTPException

from ..lib.arxiv import ArxivClient, generate_first_page_thumbnail
from ..schema.arxiv import ArxivEntry, ThumbnailResponse
from ..core.logger import SingletonLogger


logger = SingletonLogger().get_logger()
client = ArxivClient()


async def search_arxiv(
    search_query: str,
    start: int = 0,
    max_results: int = 10,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
) -> List[ArxivEntry]:
    try:
        results = client.search(
            search_query=search_query,
            start=start,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return [ArxivEntry.model_validate(r) for r in results]
    except Exception as e:
        logger.error(f"Arxiv search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search arXiv")


async def feed_topics(
    topics: List[str],
    start: int = 0,
    max_results: int = 10,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    user_id: Optional[int] = None,
) -> List[ArxivEntry]:
    try:
        results = client.feed_by_topics(
            topics=topics,
            start=start,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        entries = [ArxivEntry.model_validate(r) for r in results]

        # Optionally generate thumbnails for each entry's PDF in parallel
        if user_id is not None and entries:
            import asyncio

            tasks = [
                (
                    generate_first_page_thumbnail(
                        pdf_url=e.pdf_url or "",
                        user_id=user_id,
                        target_width=400,
                        folder="thumbnails",
                    )
                    if e.pdf_url
                    else asyncio.sleep(0)
                )  # noop to keep indexing consistent
                for e in entries
            ]
            urls = await asyncio.gather(*tasks)
            for e, url in zip(entries, urls):
                if url:
                    e.thumbnail_url = url

        return entries
    except Exception as e:
        logger.error(f"Arxiv topic feed failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch arXiv feed")


async def feed_topic_string(
    topics_csv: str,
    start: int = 0,
    max_results: int = 10,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    user_id: Optional[int] = None,
) -> List[ArxivEntry]:
    try:
        results = client.feed_by_topic_string(
            topics_csv=topics_csv,
            start=start,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        entries = [ArxivEntry.model_validate(r) for r in results]

        # Optionally generate thumbnails for each entry's PDF in parallel
        if user_id is not None and entries:
            import asyncio

            tasks = [
                (
                    generate_first_page_thumbnail(
                        pdf_url=e.pdf_url or "",
                        user_id=user_id,
                        target_width=400,
                        folder="thumbnails",
                    )
                    if e.pdf_url
                    else asyncio.sleep(0)
                )
                for e in entries
            ]
            urls = await asyncio.gather(*tasks)
            for e, url in zip(entries, urls):
                if url:
                    e.thumbnail_url = url

        return entries
    except Exception as e:
        logger.error(f"Arxiv topic-string feed failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch arXiv feed")


async def create_pdf_thumbnail(
    user_id: int,
    pdf_url: str,
    target_width: int = 400,
    folder: str = "thumbnails",
) -> ThumbnailResponse:
    try:
        url = await generate_first_page_thumbnail(
            pdf_url=pdf_url,
            user_id=user_id,
            target_width=target_width,
            folder=folder,
        )
        if not url:
            raise HTTPException(status_code=400, detail="Unable to generate thumbnail")
        return ThumbnailResponse(thumbnail_url=url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate thumbnail")
