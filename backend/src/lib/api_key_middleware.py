"""
Dependency to load decrypted API keys from user settings into request state.
"""

import os
from typing import Optional
from fastapi import Request, Depends
from cryptography.fernet import Fernet
from ..core.logger import SingletonLogger
from .auth import get_current_user

logger = SingletonLogger().get_logger()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is not set")

fernet = Fernet(ENCRYPTION_KEY.encode())


async def load_user_api_keys(
    request: Request, user_id: int = Depends(get_current_user)
) -> int:
    """
    Dependency that loads the current user's API keys into request.state.
    Explicitly depends on get_current_user to ensure user is authenticated first.

    Args:
        request: FastAPI Request object
        user_id: The authenticated user ID (from get_current_user dependency)

    Returns:
        The user_id
    """
    # Initialize empty dict if not already present
    if not hasattr(request.state, "decrypted_api_keys"):
        request.state.decrypted_api_keys = {}

    try:
        from ..database.db import session_pool
        from ..model.user_settings import UserSettings
        from sqlalchemy import select

        async with session_pool() as session:
            stmt = select(UserSettings).where(UserSettings.user_id == user_id)
            result = await session.execute(stmt)
            user_settings = result.scalar_one_or_none()

            if user_settings:
                # Get decrypted API keys
                api_keys = user_settings.api_keys
                if api_keys:
                    decrypted_keys = {}
                    for item in api_keys:
                        slug = item.get("slug")
                        api_key = item.get("api_key")
                        if slug and api_key:
                            decrypted_keys[slug] = api_key
                    request.state.decrypted_api_keys = decrypted_keys
                    logger.debug(
                        f"Loaded {len(decrypted_keys)} API key(s) for user {user_id}: {list(decrypted_keys.keys())}"
                    )
                else:
                    logger.debug(f"No API keys found for user {user_id}")
            else:
                logger.debug(f"No user settings found for user {user_id}")
    except Exception as e:
        logger.error(f"Error loading user API keys: {e}")

    return user_id


def get_decrypted_api_key(request: Request, service_slug: str) -> Optional[str]:
    """
    Helper function to retrieve a decrypted API key from request state.

    Args:
        request: FastAPI Request object
        service_slug: The service slug (e.g., 'groq', 'gemini', 'openrouter')

    Returns:
        The decrypted API key if found, None otherwise
    """
    if hasattr(request.state, "decrypted_api_keys"):
        return request.state.decrypted_api_keys.get(service_slug)
    return None
