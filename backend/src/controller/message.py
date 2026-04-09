from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.message import Message
from ..schema.message import MessageCreate, MessageUpdate, MessageResponse
from ..schema.source import SourceResponse
from ..core.logger import SingletonLogger


logger = SingletonLogger().get_logger()


async def create_message(user_id: int, payload: MessageCreate) -> MessageResponse:
    """Create a new message in a session."""
    try:
        async with session_pool() as session:
            message = Message(
                session_id=payload.session_id,
                user_id=user_id if payload.user_id is None else payload.user_id,
                content=payload.content,
                parent_message_id=payload.parent_message_id,
                model_used=payload.model_used,
                confidence_score=payload.confidence_score,
                liked=payload.liked,
                feedback=payload.feedback,
                stars=payload.stars,
                generation_metadata=payload.generation_metadata,
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)

            return MessageResponse(
                id=message.id,
                session_id=message.session_id,
                user_id=message.user_id,
                content=message.content,
                parent_message_id=message.parent_message_id,
                model_used=message.model_used,
                confidence_score=message.confidence_score,
                liked=message.liked,
                feedback=message.feedback,
                stars=message.stars,
                generation_metadata=message.generation_metadata,
                created_at=message.created_at,
                updated_at=message.updated_at,
                sources=[],
            )
    except DBAPIError as e:
        logger.exception(
            f"Database connection error creating message for session_id={payload.session_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error creating message for session_id={payload.session_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to create message")
    except Exception as e:
        logger.error(
            f"Unexpected error creating message for session_id={payload.session_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_message(message_id: int, user_id: int) -> MessageResponse:
    """Retrieve a message by ID, ensuring it belongs to the user's session."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Message)
                .where(Message.id == message_id)
                .options(selectinload(Message.sources))
            )
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")

            return MessageResponse(
                id=message.id,
                session_id=message.session_id,
                user_id=message.user_id,
                content=message.content,
                parent_message_id=message.parent_message_id,
                model_used=message.model_used,
                confidence_score=message.confidence_score,
                liked=message.liked,
                feedback=message.feedback,
                stars=message.stars,
                generation_metadata=message.generation_metadata,
                created_at=message.created_at,
                updated_at=message.updated_at,
                sources=[
                    SourceResponse(
                        id=source.id,
                        message_id=source.message_id,
                        source_text=source.source_text,
                        source_type=source.source_type,
                        source_url=source.source_url,
                        metadata=source.source_metadata,
                        created_at=source.created_at,
                        updated_at=source.updated_at,
                    )
                    for source in message.sources
                ],
            )
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error retrieving message id={message_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving message id={message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve message")
    except Exception as e:
        logger.error(f"Unexpected error retrieving message id={message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_messages_by_session(
    session_id: int, user_id: int
) -> list[MessageResponse]:
    """Retrieve all messages for a session."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .options(selectinload(Message.sources))
                .order_by(Message.created_at)
            )
            messages = result.scalars().all()
            return [
                MessageResponse(
                    id=message.id,
                    session_id=message.session_id,
                    user_id=message.user_id,
                    content=message.content,
                    parent_message_id=message.parent_message_id,
                    model_used=message.model_used,
                    confidence_score=message.confidence_score,
                    liked=message.liked,
                    feedback=message.feedback,
                    stars=message.stars,
                    generation_metadata=message.generation_metadata,
                    created_at=message.created_at,
                    updated_at=message.updated_at,
                    sources=[
                        SourceResponse(
                            id=source.id,
                            message_id=source.message_id,
                            source_text=source.source_text,
                            source_type=source.source_type,
                            source_url=source.source_url,
                            metadata=source.source_metadata,
                            created_at=source.created_at,
                            updated_at=source.updated_at,
                        )
                        for source in message.sources
                    ],
                )
                for message in messages
            ]
    except DBAPIError as e:
        logger.exception(
            f"Database connection error retrieving messages for session_id={session_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error retrieving messages for session_id={session_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving messages for session_id={session_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_message(
    message_id: int, user_id: int, payload: MessageUpdate
) -> MessageResponse:
    """Update a message's content or feedback fields."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Message).where(Message.id == message_id)
            )
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")

            # Update fields only if provided
            if payload.content is not None:
                message.content = payload.content
            if payload.liked is not None:
                message.liked = payload.liked
            if payload.feedback is not None:
                message.feedback = payload.feedback
            if payload.stars is not None:
                message.stars = payload.stars

            await session.commit()
            # Reload message with sources eagerly loaded
            result = await session.execute(
                select(Message)
                .where(Message.id == message.id)
                .options(selectinload(Message.sources))
            )
            message = result.scalar_one()

            return MessageResponse(
                id=message.id,
                session_id=message.session_id,
                user_id=message.user_id,
                content=message.content,
                parent_message_id=message.parent_message_id,
                model_used=message.model_used,
                confidence_score=message.confidence_score,
                liked=message.liked,
                feedback=message.feedback,
                stars=message.stars,
                generation_metadata=message.generation_metadata,
                created_at=message.created_at,
                updated_at=message.updated_at,
                sources=[
                    SourceResponse(
                        id=source.id,
                        message_id=source.message_id,
                        source_text=source.source_text,
                        source_type=source.source_type,
                        source_url=source.source_url,
                        metadata=source.source_metadata,
                        created_at=source.created_at,
                        updated_at=source.updated_at,
                    )
                    for source in message.sources
                ],
            )
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error updating message id={message_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error updating message id={message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update message")
    except Exception as e:
        logger.error(f"Unexpected error updating message id={message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def delete_message(message_id: int, user_id: int) -> None:
    """Delete a message by ID."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Message).where(Message.id == message_id)
            )
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")

            await session.delete(message)
            await session.commit()
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error deleting message id={message_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting message id={message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete message")
    except Exception as e:
        logger.error(f"Unexpected error deleting message id={message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
