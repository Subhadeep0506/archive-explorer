"""
FastAPI dependencies for request processing.
"""

from typing import Optional
from fastapi import Request, Depends
from ..lib.auth import get_current_user
from ..database.db import session_pool
from ..controller.user_settings import UserSettingsController
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


async def load_user_api_keys(
    request: Request, user_id: int = Depends(get_current_user)
) -> None:
    """
    FastAPI dependency that loads and decrypts user's API keys from database.

    This is a FALLBACK mechanism. The primary decryption happens in APIKeyDecryptionMiddleware
    which decrypts api_keys_encrypted from the request body sent by the frontend.

    This dependency:
    1. Checks if middleware already decrypted keys (from request body)
    2. If not, falls back to fetching from database (for requests without api_keys_encrypted)
    3. Decrypts them using the UserSettings model property
    4. Stores decrypted keys in request.state.decrypted_api_keys

    Args:
        request: FastAPI Request object
        user_id: Authenticated user ID from get_current_user dependency
    """
    if not hasattr(request.state, "decrypted_api_keys"):
        request.state.decrypted_api_keys = {}

    if request.state.decrypted_api_keys:
        logger.info(
            f"API keys already decrypted by middleware ({len(request.state.decrypted_api_keys)} keys), skipping DB fetch"
        )
        return
    try:
        async with session_pool() as session:
            user_settings = await UserSettingsController.get_user_settings(
                session, user_id
            )
            if user_settings and user_settings.api_keys:
                api_keys_list = user_settings.api_keys

                if api_keys_list:
                    for item in api_keys_list:
                        slug = item.get("slug")
                        api_key = item.get("api_key")
                        if slug and api_key:
                            request.state.decrypted_api_keys[slug] = api_key

                    logger.info(
                        f"Loaded {len(request.state.decrypted_api_keys)} API keys for user {user_id}: "
                        f"{list(request.state.decrypted_api_keys.keys())}"
                    )
    except Exception as e:
        logger.error(f"Error loading user API keys: {e}")
