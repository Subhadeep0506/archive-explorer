from fastapi import APIRouter, Depends

from ..controller import session as session_controller
from ..schema.session import SessionCreate, SessionUpdate, SessionResponse
from ..lib.auth import get_current_user


router = APIRouter()


@router.get("/", response_model=list[SessionResponse])
async def get_user_sessions_endpoint(user_id: int = Depends(get_current_user)):
    """Retrieve all sessions for the current user."""
    return await session_controller.get_sessions_by_user(user_id)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(
    session_id: int, user_id: int = Depends(get_current_user)
):
    """Retrieve a specific session by ID."""
    return await session_controller.get_session(session_id, user_id)


@router.post("/", response_model=SessionResponse)
async def create_session_endpoint(
    payload: SessionCreate, user_id: int = Depends(get_current_user)
):
    """Create a new session for the current user."""
    return await session_controller.create_session(user_id, payload)


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session_endpoint(
    session_id: int, payload: SessionUpdate, user_id: int = Depends(get_current_user)
):
    """Update an existing session."""
    return await session_controller.update_session(session_id, user_id, payload)


@router.delete("/{session_id}", status_code=204)
async def delete_session_endpoint(
    session_id: int, user_id: int = Depends(get_current_user)
):
    """Delete a session by ID."""
    await session_controller.delete_session(session_id, user_id)
