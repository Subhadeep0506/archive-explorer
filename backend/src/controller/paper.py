from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from fastapi import HTTPException

from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.paper import Paper
from ..schema.paper import PaperCreate, PaperResponse
from ..core.logger import SingletonLogger
from ..core.ingest_engine.ingestion import IngestionEngine
from ..lib.arxiv import generate_first_page_thumbnail


logger = SingletonLogger().get_logger()


async def create_paper(user_id: int, payload: PaperCreate) -> PaperResponse:
    """Create a paper entry and automatically generate thumbnail."""
    try:
        async with session_pool() as session:
            # Prevent duplicates by arxiv_id
            existing = await session.execute(
                select(Paper).where(Paper.arxiv_id == payload.arxiv_id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Paper already exists")

            paper = Paper(
                user_id=user_id,
                title=payload.title,
                abstract=payload.abstract,
                authors=payload.authors,
                arxiv_id=payload.arxiv_id,
                pdf_url=payload.pdf_url,
                paper_url=payload.paper_url,
                github_url=payload.github_url,
                topics=payload.topics,
                published_date=payload.published_date,
                institution=payload.institution,
                date_published=payload.date_published,
                paper_summary="",
            )
            session.add(paper)
            await session.commit()
            await session.refresh(paper)

            # Generate thumbnail after initial insert
            try:
                thumb_url = await generate_first_page_thumbnail(
                    pdf_url=paper.pdf_url, user_id=user_id, target_width=400
                )
                if thumb_url:
                    paper.thumbnail_url = thumb_url
                    await session.commit()
                    await session.refresh(paper)
            except Exception as e:
                # Non-fatal; keep paper even if thumbnail fails
                logger.warning(
                    f"Thumbnail generation failed for arxiv_id={paper.arxiv_id}: {str(e)}"
                )

            return PaperResponse(
                id=paper.id,
                user_id=paper.user_id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                arxiv_id=paper.arxiv_id,
                pdf_url=paper.pdf_url,
                paper_url=paper.paper_url,
                github_url=paper.github_url,
                topics=paper.topics,
                published_date=paper.published_date,
                thumbnail_url=paper.thumbnail_url,
                institution=paper.institution,
                date_published=paper.date_published,
                created_at=paper.created_at,
                ingested=paper.ingested,
                paper_summary=paper.paper_summary,
            )
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error creating paper arxiv_id={payload.arxiv_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error creating paper arxiv_id={payload.arxiv_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to create paper")
    except Exception as e:
        logger.error(
            f"Unexpected error creating paper arxiv_id={payload.arxiv_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_paper(paper_id: int, user_id: int) -> PaperResponse:
    """Retrieve a paper by ID, ensuring it belongs to the user."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                raise HTTPException(status_code=404, detail="Paper not found")

            return PaperResponse(
                id=paper.id,
                user_id=paper.user_id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                arxiv_id=paper.arxiv_id,
                pdf_url=paper.pdf_url,
                paper_url=paper.paper_url,
                github_url=paper.github_url,
                topics=paper.topics,
                published_date=paper.published_date,
                thumbnail_url=paper.thumbnail_url,
                institution=paper.institution,
                date_published=paper.date_published,
                created_at=paper.created_at,
                ingested=paper.ingested,
                paper_summary=paper.paper_summary,
            )
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error retrieving paper id={paper_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving paper id={paper_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve paper")
    except Exception as e:
        logger.error(f"Unexpected error retrieving paper id={paper_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_all_papers(user_id: int) -> list[PaperResponse]:
    """Retrieve all papers for a user."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Paper).where(Paper.user_id == user_id)
            )
            papers = result.scalars().all()
            return [
                PaperResponse(
                    id=paper.id,
                    user_id=paper.user_id,
                    title=paper.title,
                    abstract=paper.abstract,
                    authors=paper.authors,
                    arxiv_id=paper.arxiv_id,
                    pdf_url=paper.pdf_url,
                    paper_url=paper.paper_url,
                    github_url=paper.github_url,
                    topics=paper.topics,
                    published_date=paper.published_date,
                    thumbnail_url=paper.thumbnail_url,
                    institution=paper.institution,
                    date_published=paper.date_published,
                    created_at=paper.created_at,
                    ingested=paper.ingested,
                    paper_summary=paper.paper_summary,
                )
                for paper in papers
            ]
    except DBAPIError as e:
        logger.exception(
            f"Database connection error retrieving papers for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error retrieving papers for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve papers")
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving papers for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_paper(
    paper_id: int, user_id: int, payload: PaperCreate
) -> PaperResponse:
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                raise HTTPException(status_code=404, detail="Paper not found")

            # Update fields
            paper.title = payload.title
            paper.abstract = payload.abstract
            paper.authors = payload.authors
            paper.arxiv_id = payload.arxiv_id
            paper.pdf_url = payload.pdf_url
            paper.paper_url = payload.paper_url
            paper.github_url = payload.github_url
            paper.topics = payload.topics
            paper.published_date = payload.published_date
            paper.institution = payload.institution
            paper.date_published = payload.date_published

            await session.commit()
            await session.refresh(paper)

            return PaperResponse(
                id=paper.id,
                user_id=paper.user_id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                arxiv_id=paper.arxiv_id,
                pdf_url=paper.pdf_url,
                paper_url=paper.paper_url,
                github_url=paper.github_url,
                topics=paper.topics,
                published_date=paper.published_date,
                thumbnail_url=paper.thumbnail_url,
                institution=paper.institution,
                date_published=paper.date_published,
                created_at=paper.created_at,
                ingested=paper.ingested,
                paper_summary=paper.paper_summary,
            )
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error updating paper id={paper_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))


async def delete_paper(paper_id: int, user_id: int) -> None:
    """Delete a paper by ID, ensuring it belongs to the user."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                raise HTTPException(status_code=404, detail="Paper not found")

            arxiv_ids = [paper.arxiv_id] if paper.arxiv_id else []
            await _cleanup_ingested_content(arxiv_ids)
            await session.delete(paper)
            await session.commit()
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error deleting paper id={paper_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting paper id={paper_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete paper")
    except Exception as e:
        logger.error(f"Unexpected error deleting paper id={paper_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def bulk_delete_papers(paper_ids: list[int], user_id: int) -> dict:
    """Delete multiple papers by IDs, ensuring they belong to the user."""
    try:
        async with session_pool() as session:
            # Check which papers exist and belong to user
            result = await session.execute(
                select(Paper).where(Paper.id.in_(paper_ids), Paper.user_id == user_id)
            )
            papers = result.scalars().all()
            found_ids = {p.id for p in papers}
            not_found = set(paper_ids) - found_ids
            if not_found:
                raise HTTPException(
                    status_code=404, detail=f"Papers not found: {list(not_found)}"
                )

            await _cleanup_ingested_content(
                [paper.arxiv_id for paper in papers if paper.arxiv_id]
            )
            # Delete them
            for paper in papers:
                await session.delete(paper)
            await session.commit()
        return {"message": f"Deleted {len(papers)} papers"}
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error deleting papers ids={paper_ids}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting papers ids={paper_ids}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete papers")
    except Exception as e:
        logger.error(f"Unexpected error deleting papers ids={paper_ids}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _cleanup_ingested_content(arxiv_ids: list[str]) -> None:
    """Remove any ingested artifacts for the provided arXiv identifiers."""
    if not arxiv_ids:
        return

    try:
        await IngestionEngine.delete_paper_using_paper_ids(arxiv_ids)
    except Exception as e:
        logger.warning(
            "Failed to delete ingested content for arxiv_ids=%s: %s",
            ", ".join(arxiv_ids),
            e,
        )
