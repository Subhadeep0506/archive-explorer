"""
Middleware to decrypt API keys from request payload and attach to request state.
"""

import os
import json
from typing import Optional
from fastapi import Request, Response
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Scope, Receive, Send, Message
from cryptography.fernet import Fernet
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is not set")

fernet = Fernet(ENCRYPTION_KEY.encode())


class APIKeyDecryptionMiddleware:
    """
    Middleware that decrypts encrypted API keys from request body and stores them in request.state.

    This middleware:
    1. Checks if the request contains 'api_keys_encrypted' in the body
    2. Decrypts each API key using Fernet encryption
    3. Stores decrypted keys in request.state.decrypted_api_keys for use by controllers

    The decrypted keys are stored as a dictionary: {service_slug: api_key_value}
    Example: {'groq': 'gsk_...', 'gemini': 'AIza...'}
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["decrypted_api_keys"] = {}
        method = scope.get("method", "")
        if method in ["POST", "PUT", "PATCH"]:
            body_parts = []
            body_complete = False

            async def receive_wrapper() -> Message:
                nonlocal body_complete
                message = await receive()

                if message["type"] == "http.request":
                    body = message.get("body", b"")
                    if body:
                        body_parts.append(body)

                    if not message.get("more_body", False):
                        body_complete = True
                        full_body = b"".join(body_parts)
                        self._process_api_keys(full_body, scope)

                return message
            await self.app(scope, receive_wrapper, send)
        else:
            await self.app(scope, receive, send)

    def _process_api_keys(self, body_bytes: bytes, scope: Scope) -> None:
        """Process and decrypt API keys from request body."""
        if not body_bytes:
            return

        try:
            body_json = json.loads(body_bytes)
            if "api_keys_encrypted" in body_json:
                api_keys_encrypted = body_json.get("api_keys_encrypted")
                logger.debug(
                    f"Found api_keys_encrypted in request: {len(api_keys_encrypted) if api_keys_encrypted else 0} keys"
                )

                if api_keys_encrypted and isinstance(api_keys_encrypted, list):
                    decrypted_keys = {}

                    for item in api_keys_encrypted:
                        if isinstance(item, dict):
                            slug = item.get("slug")
                            encrypted_key = item.get("api_key")

                            if slug and encrypted_key:
                                try:
                                    decrypted_key = fernet.decrypt(
                                        encrypted_key.encode()
                                    ).decode()
                                    decrypted_keys[slug] = decrypted_key
                                    logger.debug(
                                        f"Successfully decrypted API key for service '{slug}'"
                                    )
                                except Exception as decrypt_error:
                                    logger.error(
                                        f"Failed to decrypt API key for service '{slug}': {decrypt_error}"
                                    )
                    scope["state"]["decrypted_api_keys"] = decrypted_keys
                    if decrypted_keys:
                        logger.info(
                            f"Successfully decrypted {len(decrypted_keys)} API key(s): {list(decrypted_keys.keys())}"
                        )
                    else:
                        logger.warning("No API keys were successfully decrypted")
            else:
                logger.debug("No api_keys_encrypted field in request body")

        except json.JSONDecodeError:
            logger.debug("Request body is not JSON, skipping API key processing")
        except Exception as e:
            logger.error(f"Error processing API keys: {e}")


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
