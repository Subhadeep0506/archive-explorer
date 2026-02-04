from typing import List, Optional
from fastapi import HTTPException

from ..lib.arxiv import (
    ArxivClient,
    generate_first_page_thumbnail,
    get_existing_thumbnail_url,
)
from ..schema.arxiv import ArxivEntry, ThumbnailResponse
from ..core.logger import SingletonLogger


logger = SingletonLogger().get_logger()
client = ArxivClient()


async def _warm_thumbnails(entries: List[ArxivEntry], user_id: int) -> None:
    """Generate missing thumbnails in the background with limited concurrency."""
    import asyncio

    sem = asyncio.Semaphore(3)

    async def worker(e: ArxivEntry):
        if not e.pdf_url:
            return
        if getattr(e, "thumbnail_url", None):
            return
        async with sem:
            try:
                await generate_first_page_thumbnail(
                    pdf_url=e.pdf_url,
                    user_id=user_id,
                    target_width=400,
                    folder="thumbnails",
                )
            except Exception:
                # Best-effort; swallow exceptions
                pass

    await asyncio.gather(*(worker(e) for e in entries))


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
    include_thumbnails: bool = False,
    max_thumbnail_concurrency: int = 3,
    thumbnail_timeout_sec: int = 20,
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

        # Populate thumbnails based on request preference
        if user_id is not None and entries:
            import asyncio

            if include_thumbnails:
                sem = asyncio.Semaphore(max(1, max_thumbnail_concurrency))

                async def gen(e: ArxivEntry):
                    if not e.pdf_url:
                        return None
                    cached = await get_existing_thumbnail_url(
                        pdf_url=e.pdf_url,
                        user_id=user_id,
                        folder="thumbnails",
                    )
                    if cached:
                        return cached
                    async with sem:
                        try:
                            return await asyncio.wait_for(
                                generate_first_page_thumbnail(
                                    pdf_url=e.pdf_url,
                                    user_id=user_id,
                                    target_width=1024,
                                    folder="thumbnails",
                                ),
                                timeout=thumbnail_timeout_sec,
                            )
                        except Exception:
                            return None

                urls = await asyncio.gather(*(gen(e) for e in entries))
                for e, url in zip(entries, urls):
                    if url:
                        e.thumbnail_url = url
            else:
                tasks = [
                    (
                        get_existing_thumbnail_url(
                            pdf_url=e.pdf_url or "",
                            user_id=user_id,
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

                missing = [
                    e
                    for e in entries
                    if e.pdf_url and not getattr(e, "thumbnail_url", None)
                ]
                if missing:
                    asyncio.create_task(_warm_thumbnails(missing, user_id))

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
    include_thumbnails: bool = False,
    max_thumbnail_concurrency: int = 3,
    thumbnail_timeout_sec: int = 20,
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

        # Populate thumbnails based on request preference
        if user_id is not None and entries:
            import asyncio

            if include_thumbnails:
                sem = asyncio.Semaphore(max(1, max_thumbnail_concurrency))

                async def gen(e: ArxivEntry):
                    if not e.pdf_url:
                        return None
                    cached = await get_existing_thumbnail_url(
                        pdf_url=e.pdf_url,
                        user_id=user_id,
                        folder="thumbnails",
                    )
                    if cached:
                        return cached
                    async with sem:
                        try:
                            return await asyncio.wait_for(
                                generate_first_page_thumbnail(
                                    pdf_url=e.pdf_url,
                                    user_id=user_id,
                                    target_width=1024,
                                    folder="thumbnails",
                                ),
                                timeout=thumbnail_timeout_sec,
                            )
                        except Exception:
                            return None

                urls = await asyncio.gather(*(gen(e) for e in entries))
                for e, url in zip(entries, urls):
                    if url:
                        e.thumbnail_url = url
            else:
                tasks = [
                    (
                        get_existing_thumbnail_url(
                            pdf_url=e.pdf_url or "",
                            user_id=user_id,
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

                missing = [
                    e
                    for e in entries
                    if e.pdf_url and not getattr(e, "thumbnail_url", None)
                ]
                if missing:
                    asyncio.create_task(_warm_thumbnails(missing, user_id))

        return entries
    except Exception as e:
        logger.error(f"Arxiv topic-string feed failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch arXiv feed")


async def create_pdf_thumbnail(
    user_id: int,
    pdf_url: str,
    target_width: int = 1024,
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
