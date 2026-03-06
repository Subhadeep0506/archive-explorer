from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from fastapi import HTTPException
from typing import List

from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.source import Source
from ..schema.source import SourceCreate, SourceResponse
from ..core.logger import SingletonLogger


logger = SingletonLogger().get_logger()


async def create_sources(sources: List[SourceCreate]) -> List[SourceResponse]:
    """Create multiple sources for a message in bulk."""
    if not sources:
        return []

    try:
        async with session_pool() as session:
            source_objects = [
                Source(
                    message_id=source.message_id,
                    source_text=source.source_text,
                    source_type=source.source_type,
                    source_url=source.source_url,
                )
                for source in sources
            ]
            session.add_all(source_objects)
            await session.commit()

            # Refresh all objects to get IDs and timestamps
            for source_obj in source_objects:
                await session.refresh(source_obj)

            return [
                SourceResponse(
                    id=source.id,
                    message_id=source.message_id,
                    source_text=source.source_text,
                    source_type=source.source_type,
                    source_url=source.source_url,
                    created_at=source.created_at,
                    updated_at=source.updated_at,
                )
                for source in source_objects
            ]
    except DBAPIError as e:
        logger.exception(f"Database connection error creating sources: {str(e)}")
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error creating sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create sources")
    except Exception as e:
        logger.error(f"Unexpected error creating sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_sources_by_message(message_id: int) -> List[SourceResponse]:
    """Retrieve all sources for a specific message."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Source)
                .where(Source.message_id == message_id)
                .order_by(Source.created_at)
            )
            sources = result.scalars().all()
            return [
                SourceResponse(
                    id=source.id,
                    message_id=source.message_id,
                    source_text=source.source_text,
                    source_type=source.source_type,
                    source_url=source.source_url,
                    created_at=source.created_at,
                    updated_at=source.updated_at,
                )
                for source in sources
            ]
    except DBAPIError as e:
        logger.exception(
            f"Database connection error retrieving sources for message_id={message_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error retrieving sources for message_id={message_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve sources")
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving sources for message_id={message_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
