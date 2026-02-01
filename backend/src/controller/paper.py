from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from fastapi import HTTPException

from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.paper import Paper
from ..schema.paper import PaperCreate, PaperResponse
from ..core.logger import SingletonLogger
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
