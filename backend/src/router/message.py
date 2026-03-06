from fastapi import APIRouter, Depends
from typing import List

from ..controller import message as message_controller
from ..schema.message import MessageUpdate, MessageResponse
from ..lib.auth import get_current_user


router = APIRouter()


@router.get("/session/{session_id}", response_model=list[MessageResponse])
async def get_messages_by_session_endpoint(
    session_id: int, user_id: int = Depends(get_current_user)
):
    """Retrieve all messages for a specific session."""
    return await message_controller.get_messages_by_session(session_id, user_id)


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message_endpoint(
    message_id: int, user_id: int = Depends(get_current_user)
):
    """Retrieve a specific message by ID."""
    return await message_controller.get_message(message_id, user_id)


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message_endpoint(
    message_id: int, payload: MessageUpdate, user_id: int = Depends(get_current_user)
):
    """Update a message's content or feedback fields."""
    return await message_controller.update_message(message_id, user_id, payload)


@router.delete("/{message_id}", status_code=204)
async def delete_message_endpoint(
    message_id: int, user_id: int = Depends(get_current_user)
):
    """Delete a message by ID."""
    await message_controller.delete_message(message_id, user_id)
