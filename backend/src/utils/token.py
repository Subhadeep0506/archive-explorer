import os
from jose import jwt, JWTError
from typing import Dict, Any
from ..core.logger import SingletonLogger


def decodeJWT(token: str) -> Dict[str, Any] | None:
    """
    Decode and verify a JWT token.

    Args:
        token: The JWT token string to decode

    Returns:
        Dict containing the token payload if valid, None otherwise
    """
    try:
        decoded_token = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=[os.getenv("JWT_ALGORITHM")],
        )
        return decoded_token
    except JWTError as e:
        SingletonLogger().get_logger().error(f"JWT decode error: {e}")
        return None