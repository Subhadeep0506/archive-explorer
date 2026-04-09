from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, Request
from typing import Optional

from ..core.ingest_engine.ingestion import IngestionEngine
from ..schema.ingestion import PaperIngest, PaperDelete
from ..core.logger import SingletonLogger
from ..database.db import session_pool
from ..model.paper import Paper

logger = SingletonLogger().get_logger()


async def ingest_paper(payload: PaperIngest, user_id: int, request: Optional[Request] = None) -> dict:
    """Ingest a paper into the vector store using the provided URL."""
    try:
        await IngestionEngine.ingest_paper_using_paper_id(
            paper_id=payload.arxiv_id,
            paper_url=payload.paper_url,
            embedding_model=payload.embedding_model,
            request=request,
        )
        await _set_ingested_flag(
            user_id=user_id,
            arxiv_ids=[payload.arxiv_id] if payload.arxiv_id else None,
            paper_url=payload.paper_url,
            ingested=True,
        )
        return {"message": "Paper ingested successfully"}
    except ValueError as e:
        # Handle validation errors (like missing API keys)
        error_msg = str(e)
        logger.error(f"Validation error ingesting paper: {error_msg}")
        raise HTTPException(
            status_code=422,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Error ingesting paper: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e) if str(e) else "Failed to ingest paper"
        )


async def delete_paper(payload: PaperDelete, user_id: int, request: Optional[Request] = None) -> dict:
    """Delete a paper from the vector store using the paper ID."""
    try:
        await IngestionEngine.delete_paper_using_paper_ids(paper_ids=payload.paper_ids, request=request)
        await _set_ingested_flag(
            user_id=user_id,
            arxiv_ids=payload.paper_ids,
            ingested=False,
        )
        return {"message": "Paper deleted successfully"}
    except ValueError as e:
        # Handle validation errors (like missing API keys)
        error_msg = str(e)
        logger.error(f"Validation error deleting paper: {error_msg}")
        raise HTTPException(
            status_code=422,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Error deleting paper: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e) if str(e) else "Failed to delete paper"
        )


async def _set_ingested_flag(
    *,
    user_id: int,
    ingested: bool,
    arxiv_ids: list[str] | None = None,
    paper_url: str | None = None,
) -> None:
    """Update the ingested flag for a user's paper, if it exists."""
    if not arxiv_ids and not paper_url:
        return

    try:
        async with session_pool() as session:
            stmt = select(Paper).where(Paper.user_id == user_id)
            if arxiv_ids:
                stmt = stmt.where(Paper.arxiv_id.in_(arxiv_ids))
            else:
                stmt = stmt.where(Paper.pdf_url == paper_url)

            result = await session.execute(stmt)
            papers = result.scalars().all()
            if not papers:
                logger.warning(
                    "Unable to update ingested flag; paper(s) not found for user_id=%s target=%s",
                    user_id,
                    ", ".join(arxiv_ids) if arxiv_ids else paper_url or "<unknown>",
                )
                return

            for paper in papers:
                paper.ingested = ingested
            await session.commit()
    except SQLAlchemyError as db_err:
        logger.error(
            "Database error updating ingested flag for user_id=%s target=%s: %s",
            user_id,
            ", ".join(arxiv_ids) if arxiv_ids else paper_url or "<unknown>",
            db_err,
        )
