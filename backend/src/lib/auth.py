import bcrypt
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Union
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.user import User
from ..model.profile import Profile
from ..model.login_session import LoginSession
from ..utils.token import decodeJWT
from ..core.logger import SingletonLogger


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


async def build_token_payload(user: User, session: AsyncSession) -> Dict[str, Any]:
    """
    Build JWT token payload with user and profile information.

    Args:
        user: User object
        session: Database session to fetch profile

    Returns:
        Dict containing user data (excluding password)
    """
    # Get user profile
    profile_result = await session.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()

    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "google_id": user.google_id,
        "profile": (
            {
                "phone": profile.phone if profile else None,
                "avatar": profile.avatar if profile else None,
                "bio": profile.bio if profile else None,
            }
            if profile
            else None
        ),
    }

    return payload


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> tuple[str, datetime]:
    """Create JWT access token with user and profile information"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        or timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("JWT_SECRET_KEY"), algorithm=os.getenv("JWT_ALGORITHM")
    )
    return encoded_jwt, expire


def create_refresh_token(
    subject: Union[str, Any], expires_delta: timedelta | None = None
) -> tuple[str, datetime]:
    """Create JWT refresh token"""
    if expires_delta is not None:
        expires_delta_time = datetime.utcnow() + expires_delta
    else:
        expires_delta_time = datetime.utcnow() + timedelta(
            minutes=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", 10080))
        )
    to_encode = {"exp": expires_delta_time, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("JWT_SECRET_KEY"), os.getenv("JWT_ALGORITHM")
    )
    return encoded_jwt, expires_delta_time


class JWTBearer(HTTPBearer):
    """Custom JWT Bearer authentication class with token verification."""

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            logger = getattr(
                request.app.state, "logger", SingletonLogger().get_logger()
            )
            if not credentials.scheme == "Bearer":
                logger.error("Invalid authentication scheme.")
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )
            if not self.verify_jwt(credentials.credentials):
                logger.error("Invalid token or expired token.")
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            return credentials.credentials
        else:
            logger = getattr(
                request.app.state, "logger", SingletonLogger().get_logger()
            )
            logger.error("Invalid authorization code.")
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        """Verify if the JWT token is valid."""
        isTokenValid: bool = False
        try:
            payload = decodeJWT(jwtoken)
        except Exception as e:
            SingletonLogger().get_logger().error(f"JWT verification error: {e}")
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> int:
    """
    Dependency function to get current user ID from JWT token.
    Validates token against the login_session table to ensure it's still active.
    Returns the user ID for use in route dependencies.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=[os.getenv("JWT_ALGORITHM")],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        SingletonLogger().get_logger().error("JWT decode error")
        raise credentials_exception

    # Verify token is active in login_session table
    try:
        async with session_pool() as session:
            session_result = await session.execute(
                select(LoginSession)
                .filter_by(
                    user_id=int(user_id),
                    access_token=credentials.credentials,
                    is_active=True,
                )
                .order_by(desc(LoginSession.created_at))
            )
            session_record = session_result.scalar_one_or_none()

            if not session_record:
                SingletonLogger().get_logger().error(
                    f"Token not found in login_session or inactive for user {user_id}"
                )
                raise HTTPException(
                    status_code=401,
                    detail="Token is not active or has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    except (DBAPIError, SQLAlchemyError) as db_err:
        SingletonLogger().get_logger().exception(
            f"Database connection error while validating token for user {user_id}: {db_err}"
        )
        raise DatabaseConnectionError(str(db_err))

    return int(user_id)


def token_required(func):
    """
    Decorator that verifies the JWT token and checks if user is logged in.
    Validates token against the login_session table to ensure it's still active.
    Injects user_id into the function kwargs.

    Usage:
        @router.get("/protected")
        @token_required
        async def protected_route(user_id: int):
            # user_id is automatically injected
            return {"user_id": user_id}
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get request from args (first argument in FastAPI route handlers)
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        # Prepare logger (from request app.state if available)
        logger = (
            getattr(request.app.state, "logger", SingletonLogger().get_logger())
            if request
            else SingletonLogger().get_logger()
        )

        # Extract Authorization header
        auth_header = None
        if request:
            auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            logger.error("No authorization header or invalid format.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.replace("Bearer ", "")

        # Decode the token
        payload = decodeJWT(token)
        if not payload:
            logger.error("Invalid token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        if not user_id:
            logger.error("Invalid token payload.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token exists in login_session and is active
        try:
            async with session_pool() as session:
                result = await session.execute(
                    select(LoginSession)
                    .filter_by(user_id=int(user_id), access_token=token, is_active=True)
                    .order_by(desc(LoginSession.created_at))
                )
                session_record = result.scalar_one_or_none()

                if not session_record:
                    logger.error("Invalid or inactive access token.")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or inactive access token.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        except (DBAPIError, SQLAlchemyError) as db_err:
            logger.exception(
                f"Database connection error while checking token for user {user_id}: {db_err}"
            )
            raise DatabaseConnectionError(str(db_err))

        # Inject user_id into kwargs
        kwargs["user_id"] = int(user_id)
        return await func(*args, **kwargs)

    return wrapper


async def store_token_in_session(
    session: AsyncSession,
    user_id: int,
    access_token: str,
    refresh_token: str | None = None,
    login_method: str = "password",
    device_info: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    token_expires_at: datetime | None = None,
) -> LoginSession:
    """
    Store JWT tokens in the login_session table.

    Args:
        session: Database session
        user_id: ID of the user
        access_token: JWT access token
        refresh_token: JWT refresh token (optional)
        login_method: Method of login ('password', 'google', etc.)
        device_info: Device information (optional)
        ip_address: IP address (optional)
        user_agent: User agent string (optional)
        token_expires_at: Token expiration time (optional)

    Returns:
        LoginSession: The created login session record
    """
    login_session = LoginSession(
        user_id=user_id,
        login_method=login_method,
        is_active=True,
        access_token=access_token,
        refresh_token=refresh_token,
        device_info=device_info,
        ip_address=ip_address,
        user_agent=user_agent,
        token_expires_at=token_expires_at,
    )
    session.add(login_session)
    await session.commit()
    await session.refresh(login_session)
    SingletonLogger().get_logger().info(
        f"Token stored in login_session for user {user_id}"
    )
    return login_session


async def revoke_token(session: AsyncSession, access_token: str) -> bool:
    """
    Revoke a JWT token by setting the login session to inactive.

    Args:
        session: Database session
        access_token: The access token to revoke

    Returns:
        bool: True if token was revoked, False if not found
    """
    result = await session.execute(
        select(LoginSession).filter_by(access_token=access_token, is_active=True)
    )
    session_record = result.scalar_one_or_none()

    if session_record:
        session_record.is_active = False
        session_record.logout_at = datetime.utcnow()
        await session.commit()
        SingletonLogger().get_logger().info(
            f"Token revoked for user {session_record.user_id}"
        )
        return True
    SingletonLogger().get_logger().warning("Token not found or already revoked")
    return False


async def revoke_all_user_tokens(session: AsyncSession, user_id: int) -> int:
    """
    Revoke all active tokens for a specific user.

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        int: Number of tokens revoked
    """
    result = await session.execute(
        select(LoginSession).filter_by(user_id=user_id, is_active=True)
    )
    sessions = result.scalars().all()

    count = 0
    for login_session in sessions:
        login_session.is_active = False
        login_session.logout_at = datetime.utcnow()
        count += 1

    await session.commit()
    SingletonLogger().get_logger().info(f"Revoked {count} sessions for user {user_id}")
    return count
