from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from fastapi import HTTPException, Request
from typing import Optional

from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.paper import Paper
from ..model.usability import Usability
from ..schema.paper import PaperCreate, PaperResponse
from ..core.logger import SingletonLogger
from ..core.summary_engine.summary import SummaryEngine
from ..core.summary_engine.usability import UsabilityEngine


logger = SingletonLogger().get_logger()


async def get_summary_and_usability(arxiv_id: str, user_id: int) -> dict:
    """Get the summary and usability metrics for a specific paper (fetch only, no auto-generation)."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Paper).where(Paper.arxiv_id == arxiv_id)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                raise HTTPException(status_code=404, detail="Paper not found")

            summary = paper.paper_summary

            usability_result = await session.execute(
                select(Usability).where(
                    Usability.user_id == user_id, Usability.paper_id == paper.id
                )
            )
            usability = usability_result.scalar_one_or_none()

            usability_data = None
            if usability:
                usability_data = {
                    "domain_applicability": usability.domain_applicability,
                    "reproducibility_score": usability.reproducibility_score,
                    "new_tech_applicability": usability.new_tech_applicability,
                    "impact_score": usability.impact_score,
                }

            return {
                "summary": summary,
                "usability": usability_data,
            }
    except (SQLAlchemyError, DBAPIError) as e:
        logger.error(
            f"Database error while fetching summary and usability for paper {arxiv_id}: {e}"
        )
        raise DatabaseConnectionError("Failed to connect to the database")


async def generate_paper_summary(
    user_id: int,
    arxiv_id: str = None,
    pdf_url: str = None,
    request: Optional[Request] = None,
) -> str:
    """Generate a summary for a given paper and optionally update the paper_summary column."""
    try:
        # API keys are already loaded by load_user_api_keys dependency
        async with session_pool() as session:
            paper = None

            if arxiv_id:
                result = await session.execute(
                    select(Paper).where(Paper.arxiv_id == arxiv_id)
                )
                paper = result.scalar_one_or_none()
                if not paper:
                    raise HTTPException(status_code=404, detail="Paper not found")

            # Generate the summary
            summary = await SummaryEngine.generate_paper_summary(
                arxiv_id, pdf_url, request
            )

            # Only update database if we have a paper record
            if arxiv_id and paper:
                paper.paper_summary = summary
                await session.commit()
                await session.refresh(paper)

            return summary
    except (SQLAlchemyError, DBAPIError) as e:
        logger.error(
            f"Database error while generating summary for paper {arxiv_id or 'PDF URL'}: {e}"
        )
        raise DatabaseConnectionError("Failed to connect to the database")


async def generate_paper_usability(
    user_id: int,
    arxiv_id: str = None,
    pdf_url: str = None,
    request: Optional[Request] = None,
) -> dict:
    """Generate usability metrics for a given paper and store in the usability table."""
    try:
        # API keys are already loaded by load_user_api_keys dependency
        async with session_pool() as session:
            paper = None
            existing_usability = None

            if arxiv_id:
                result = await session.execute(
                    select(Paper).where(Paper.arxiv_id == arxiv_id)
                )
                paper = result.scalar_one_or_none()
                if not paper:
                    raise HTTPException(status_code=404, detail="Paper not found")

                # Check if usability record already exists for this user and paper
                usability_result = await session.execute(
                    select(Usability).where(
                        Usability.user_id == user_id, Usability.paper_id == paper.id
                    )
                )
                existing_usability = usability_result.scalar_one_or_none()

            # Generate the usability metrics
            usability_data = await UsabilityEngine.generate_paper_summary(
                arxiv_id, pdf_url, request
            )

            # Only save to database if we have a paper record (arxiv_id provided)
            if arxiv_id and paper:
                if existing_usability:
                    # Update existing record
                    existing_usability.domain_applicability = usability_data.get(
                        "domain_applicability", {}
                    )
                    existing_usability.reproducibility_score = usability_data.get(
                        "reproducibility_score", {}
                    )
                    existing_usability.new_tech_applicability = usability_data.get(
                        "new_tech_applicability", {}
                    )
                    existing_usability.impact_score = usability_data.get("impact_score")
                    await session.commit()
                    await session.refresh(existing_usability)
                else:
                    # Create new record
                    new_usability = Usability(
                        user_id=user_id,
                        paper_id=paper.id,
                        domain_applicability=usability_data.get(
                            "domain_applicability", {}
                        ),
                        reproducibility_score=usability_data.get(
                            "reproducibility_score", {}
                        ),
                        new_tech_applicability=usability_data.get(
                            "new_tech_applicability", {}
                        ),
                        impact_score=usability_data.get("impact_score"),
                    )
                    session.add(new_usability)
                    await session.commit()
                    await session.refresh(new_usability)

            return usability_data
    except (SQLAlchemyError, DBAPIError) as e:
        logger.error(
            f"Database error while generating usability for paper {arxiv_id}: {e}"
        )
        raise DatabaseConnectionError("Failed to connect to the database")
