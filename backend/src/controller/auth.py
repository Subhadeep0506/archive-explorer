from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from datetime import datetime
from fastapi import HTTPException, Request
import os
from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.user import User
from ..model.profile import Profile
from ..model.login_session import LoginSession
from ..model.user_settings import UserSettings
from ..schema.auth import RegisterRequest, LoginRequest
from ..lib.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    store_token_in_session,
)
from ..core.logger import SingletonLogger
from ..errors import *

logger = SingletonLogger().get_logger()


async def register_user(register_data: RegisterRequest):
    """Register a new user with email and password"""
    try:
        async with session_pool() as session:
            # Check if email already exists
            result = await session.execute(
                select(User).where(User.email == register_data.email)
            )
            if result.scalar_one_or_none():
                logger.warning(
                    f"Registration attempt with existing email: {register_data.email}"
                )
                raise HTTPException(status_code=400, detail="Email already registered")

            # Check if username already exists
            result = await session.execute(
                select(User).where(User.username == register_data.username)
            )
            if result.scalar_one_or_none():
                logger.warning(
                    f"Registration attempt with existing username: {register_data.username}"
                )
                raise HTTPException(status_code=400, detail="Username already taken")

            # Create new user
            hashed_password = hash_password(register_data.password)
            user = User(
                username=register_data.username,
                full_name=register_data.full_name,
                email=register_data.email,
                password=hashed_password,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Create default profile and settings for the new user
            profile = Profile(user_id=user.id)
            user_settings = UserSettings(user_id=user.id)
            session.add_all([profile, user_settings])
            await session.commit()

            logger.info(
                f"User registered successfully: {user.username} (ID: {user.id})"
            )
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
            }
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error during registration for email={register_data.email}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error during registration for email={register_data.email}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to register user")
    except Exception as e:
        logger.error(
            f"Unexpected error during registration for email={register_data.email}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def login_user(login_data: LoginRequest, request: Request):
    """Authenticate user with email and password"""
    try:
        async with session_pool() as session:
            # Find user by email
            result = await session.execute(
                select(User).where(User.email == login_data.email)
            )
            user = result.scalar_one_or_none()

            if not user or not user.password:
                logger.warning(f"Login attempt with invalid email: {login_data.email}")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            if not verify_password(login_data.password, user.password):
                logger.warning(
                    f"Login attempt with invalid password for email: {login_data.email}"
                )
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Create tokens
            access_token, token_expires_at = create_access_token(
                data={"sub": str(user.id)}
            )
            refresh_token, _ = create_refresh_token(subject=str(user.id))

            # Store tokens in login session
            login_session = await store_token_in_session(
                session=session,
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                login_method="password",
                device_info=(
                    request.headers.get("sec-ch-ua-platform", "").strip('"')
                    if request.headers.get("sec-ch-ua-platform")
                    else None
                ),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                token_expires_at=token_expires_at,
            )

            logger.info(f"User logged in successfully: {user.username} (ID: {user.id})")
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": int(
                    (token_expires_at - datetime.utcnow()).total_seconds()
                ),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                },
            }
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error during login for email={login_data.email}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error during login for email={login_data.email}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to login user")
    except Exception as e:
        logger.error(
            f"Unexpected error during login for email={login_data.email}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


oauth = AsyncOAuth2Client(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
)


async def initiate_google_login():
    """Generate Google OAuth authorization URL"""
    try:
        authorization_url, state = oauth.create_authorization_url(
            "https://accounts.google.com/o/oauth2/auth",
            scope=["openid", "email", "profile"],
        )
        logger.info("Google OAuth authorization URL generated")
        return {"authorization_url": authorization_url, "state": state}
    except Exception as e:
        logger.error(f"Error generating Google OAuth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Google login")


async def handle_google_callback(code: str, state: str, request: Request):
    """Process Google OAuth callback and authenticate/create user"""
    try:
        token = await oauth.fetch_token(
            "https://oauth2.googleapis.com/token",
            code=code,
        )

        user_info = await oauth.get("https://www.googleapis.com/oauth2/v2/userinfo")
        user_data = user_info.json()

        async with session_pool() as session:
            result = await session.execute(
                select(User).where(User.google_id == user_data["id"])
            )
            user = result.scalar_one_or_none()

            if not user:
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                user = result.scalar_one_or_none()

                if user:
                    user.google_id = user_data["id"]
                else:
                    username = user_data["email"].split("@")[0]
                    existing = await session.execute(
                        select(User).where(User.username == username)
                    )
                    if existing.scalar_one_or_none():
                        username = f"{username}_{user_data['id']}"

                    user = User(
                        username=username,
                        full_name=user_data["name"],
                        email=user_data["email"],
                        google_id=user_data["id"],
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)

                    # Create default profile and settings for the new Google user
                    profile = Profile(user_id=user.id)
                    user_settings = UserSettings(user_id=user.id)
                    session.add_all([profile, user_settings])
                    await session.commit()
            # Create tokens
            access_token, token_expires_at = create_access_token(
                data={"sub": str(user.id)}
            )
            refresh_token, _ = create_refresh_token(subject=str(user.id))

            # Store tokens in login session
            login_session = await store_token_in_session(
                session=session,
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                login_method="google",
                device_info=(
                    request.headers.get("sec-ch-ua-platform", "").strip('"')
                    if request.headers.get("sec-ch-ua-platform")
                    else None
                ),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                token_expires_at=token_expires_at,
            )

            logger.info(f"User logged in via Google: {user.username} (ID: {user.id})")
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": int(
                    (token_expires_at - datetime.utcnow()).total_seconds()
                ),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                },
            }
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error during Google OAuth callback: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error during Google OAuth callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process Google login")
    except Exception as e:
        logger.error(f"Unexpected error during Google OAuth callback: {str(e)}")
        raise HTTPException(status_code=500, detail="OAuth authentication failed")


async def logout_user(user_id: int, session_id: int | None = None):
    """Logout user by deactivating login session(s)"""
    try:
        async with session_pool() as session:
            if session_id:
                result = await session.execute(
                    select(LoginSession).where(
                        LoginSession.id == session_id,
                        LoginSession.user_id == user_id,
                        LoginSession.is_active == True,
                    )
                )
                login_session = result.scalar_one_or_none()
                if login_session:
                    login_session.is_active = False
                    login_session.logout_at = datetime.utcnow()
                    await session.commit()
                    logger.info(
                        f"User logged out: user_id={user_id}, session_id={session_id}"
                    )
                    return {"message": "Logged out successfully"}
                else:
                    logger.warning(
                        f"Logout attempt with invalid session: user_id={user_id}, session_id={session_id}"
                    )
                    raise HTTPException(
                        status_code=404, detail="Active session not found"
                    )
            else:
                result = await session.execute(
                    select(LoginSession).where(
                        LoginSession.user_id == user_id, LoginSession.is_active == True
                    )
                )
                login_sessions = result.scalars().all()
                for ls in login_sessions:
                    ls.is_active = False
                    ls.logout_at = datetime.utcnow()
                await session.commit()
                logger.info(
                    f"User logged out from all sessions: user_id={user_id}, count={len(login_sessions)}"
                )
                return {"message": f"Logged out from {len(login_sessions)} sessions"}
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error during logout for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error during logout for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to logout user")
    except Exception as e:
        logger.error(f"Unexpected error during logout for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_user_sessions(user_id: int):
    """Get all login sessions for a user"""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(LoginSession)
                .where(LoginSession.user_id == user_id)
                .order_by(LoginSession.created_at.desc())
            )
            sessions = result.scalars().all()
            return [
                {
                    "id": s.id,
                    "login_method": s.login_method,
                    "is_active": s.is_active,
                    "created_at": s.created_at,
                    "logout_at": s.logout_at,
                    "device_info": s.device_info,
                    "ip_address": s.ip_address,
                }
                for s in sessions
            ]
    except DBAPIError as e:
        logger.exception(
            f"Database connection error fetching sessions for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error fetching sessions for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve user sessions")
    except Exception as e:
        logger.error(
            f"Unexpected error fetching sessions for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def delete_user_account(user_id: int):
    """Delete a user account and all associated data"""
    try:
        async with session_pool() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                logger.warning(
                    f"Delete attempt for non-existent user: user_id={user_id}"
                )
                raise HTTPException(status_code=404, detail="User not found")

            username = user.username
            # Delete the user (cascade will handle related records)
            await session.delete(user)
            await session.commit()
            logger.info(f"User account deleted: {username} (ID: {user_id})")
            return {"message": "User account deleted successfully"}
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error deleting user account for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(
            f"Database error deleting user account for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to delete user account")
    except Exception as e:
        logger.error(
            f"Unexpected error deleting user account for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
