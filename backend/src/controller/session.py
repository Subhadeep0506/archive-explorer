from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from fastapi import HTTPException
from datetime import date

from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.chat_session import Session
from ..schema.session import SessionCreate, SessionUpdate, SessionResponse
from ..core.logger import SingletonLogger


logger = SingletonLogger().get_logger()


async def create_session(user_id: int, payload: SessionCreate) -> SessionResponse:
    """Create a new session for a user."""
    try:
        async with session_pool() as session:
            new_session = Session(
                user_id=user_id,
                paper_id=payload.paper_id,
                title=payload.title,
                started_at=payload.started_at,
                ended_at=payload.ended_at,
                device_type=payload.device_type,
            )
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)

            return SessionResponse(
                id=new_session.id,
                user_id=new_session.user_id,
                title=new_session.title,
                started_at=new_session.started_at,
                ended_at=new_session.ended_at,
                device_type=new_session.device_type,
                paper_id=new_session.paper_id,
            )
    except DBAPIError as e:
        logger.exception(
            f"Database connection error creating session for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error creating session for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to create session")
    except Exception as e:
        logger.error(
            f"Unexpected error creating session for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_session(session_id: int, user_id: int) -> SessionResponse:
    """Retrieve a session by ID, ensuring it belongs to the user."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Session).where(
                    Session.id == session_id, Session.user_id == user_id
                )
            )
            sess = result.scalar_one_or_none()
            if not sess:
                raise HTTPException(status_code=404, detail="Session not found")

            return SessionResponse(
                id=sess.id,
                user_id=sess.user_id,
                paper_id=sess.paper_id,
                title=sess.title,
                started_at=sess.started_at,
                ended_at=sess.ended_at,
                device_type=sess.device_type,
            )
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error retrieving session id={session_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving session id={session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")
    except Exception as e:
        logger.error(f"Unexpected error retrieving session id={session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_sessions_by_user(user_id: int) -> list[SessionResponse]:
    """Retrieve all sessions for a user."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Session)
                .where(Session.user_id == user_id)
                .order_by(Session.started_at.desc())
            )
            sessions = result.scalars().all()
            return [
                SessionResponse(
                    id=sess.id,
                    user_id=sess.user_id,
                    paper_id=sess.paper_id,
                    title=sess.title,
                    started_at=sess.started_at,
                    ended_at=sess.ended_at,
                    device_type=sess.device_type,
                )
                for sess in sessions
            ]
    except DBAPIError as e:
        logger.exception(
            f"Database connection error retrieving sessions for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error retrieving sessions for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving sessions for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_session_by_user_id(user_id: int):
    """Fetch the most recent session for a given user ID."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Session)
                .where(Session.user_id == user_id)
                .order_by(Session.updated_at.desc())
            )
            sess = result.scalars().first()
            return sess
    except Exception as e:
        logger.error(f"Error fetching session for user_id {user_id}: {e}")
        return None


async def update_session(
    session_id: int, user_id: int, payload: SessionUpdate
) -> SessionResponse:
    """Update an existing session with new data."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Session).where(
                    Session.id == session_id, Session.user_id == user_id
                )
            )
            sess = result.scalar_one_or_none()
            if not sess:
                raise HTTPException(status_code=404, detail="Session not found")

            # Update fields only if provided
            if payload.title is not None:
                sess.title = payload.title
            if payload.started_at is not None:
                sess.started_at = payload.started_at
            if payload.ended_at is not None:
                sess.ended_at = payload.ended_at
            if payload.device_type is not None:
                sess.device_type = payload.device_type

            await session.commit()
            await session.refresh(sess)

            return SessionResponse(
                id=sess.id,
                user_id=sess.user_id,
                paper_id=sess.paper_id,
                title=sess.title,
                started_at=sess.started_at,
                ended_at=sess.ended_at,
                device_type=sess.device_type,
            )
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error updating session id={session_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error updating session id={session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update session")
    except Exception as e:
        logger.error(f"Unexpected error updating session id={session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def delete_session(session_id: int, user_id: int) -> None:
    """Delete a session by its ID."""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Session).where(
                    Session.id == session_id, Session.user_id == user_id
                )
            )
            sess = result.scalar_one_or_none()
            if not sess:
                raise HTTPException(status_code=404, detail="Session not found")

            await session.delete(sess)
            await session.commit()
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error deleting session id={session_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting session id={session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete session")
    except Exception as e:
        logger.error(f"Unexpected error deleting session id={session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
