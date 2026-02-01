from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from fastapi import HTTPException, UploadFile
from ..database.db import session_pool
from ..errors import DatabaseConnectionError
from ..model.profile import Profile
from ..schema.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from ..core.storage import storage
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


async def get_profile(user_id: int) -> ProfileResponse:
    """Get user profile"""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")

            # Convert to dict and add avatar_url
            profile_dict = {
                "id": profile.id,
                "user_id": profile.user_id,
                "phone": profile.phone,
                "bio": profile.bio,
                "avatar_url": (
                    storage.get_file_url(profile.avatar) if profile.avatar else None
                ),
                "topic_preferences": profile.topic_preferences,
            }
            return ProfileResponse(**profile_dict)
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error fetching profile for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching profile for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")
    except Exception as e:
        logger.error(
            f"Unexpected error fetching profile for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def create_profile(user_id: int, profile_data: ProfileCreate) -> ProfileResponse:
    """Create user profile"""
    try:
        async with session_pool() as session:
            # Check if profile already exists
            result = await session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            if result.scalar_one_or_none():
                logger.warning(
                    f"Attempted to create duplicate profile for user_id={user_id}"
                )
                raise HTTPException(status_code=400, detail="Profile already exists")

            profile = Profile(user_id=user_id, **profile_data.model_dump())
            session.add(profile)
            await session.commit()
            await session.refresh(profile)

            # Return with avatar URL
            profile_dict = {
                "id": profile.id,
                "user_id": profile.user_id,
                "phone": profile.phone,
                "bio": profile.bio,
                "avatar_url": (
                    storage.get_file_url(profile.avatar) if profile.avatar else None
                ),
                "topic_preferences": profile.topic_preferences,
            }
            return ProfileResponse(**profile_dict)
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error creating profile for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error creating profile for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create profile")
    except Exception as e:
        logger.error(
            f"Unexpected error creating profile for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_profile(user_id: int, profile_data: ProfileUpdate) -> ProfileResponse:
    """Update user profile"""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")

            update_data = profile_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(profile, field, value)

            await session.commit()
            await session.refresh(profile)

            # Return with avatar URL
            profile_dict = {
                "id": profile.id,
                "user_id": profile.user_id,
                "phone": profile.phone,
                "bio": profile.bio,
                "avatar_url": (
                    storage.get_file_url(profile.avatar) if profile.avatar else None
                ),
                "topic_preferences": profile.topic_preferences,
            }
            return ProfileResponse(**profile_dict)
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error updating profile for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error updating profile for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")
    except Exception as e:
        logger.error(
            f"Unexpected error updating profile for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def upload_avatar(user_id: int, file: UploadFile) -> ProfileResponse:
    """Upload avatar for user profile"""
    try:
        async with session_pool() as session:
            result = await session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")

            # Delete old avatar if exists
            if profile.avatar:
                try:
                    await storage.delete_file(profile.avatar)
                except Exception as e:
                    logger.warning(
                        f"Failed to delete old avatar for user_id={user_id}: {str(e)}"
                    )

            # Upload new avatar
            avatar_key = await storage.upload_file(file, user_id, "avatar")

            # Update profile
            profile.avatar = avatar_key
            await session.commit()
            await session.refresh(profile)

            # Return with avatar URL
            profile_dict = {
                "id": profile.id,
                "user_id": profile.user_id,
                "phone": profile.phone,
                "bio": profile.bio,
                "avatar_url": (
                    storage.get_file_url(profile.avatar) if profile.avatar else None
                ),
                "topic_preferences": profile.topic_preferences,
            }
            return ProfileResponse(**profile_dict)
    except HTTPException:
        raise
    except DBAPIError as e:
        logger.exception(
            f"Database connection error uploading avatar for user_id={user_id}: {str(e)}"
        )
        raise DatabaseConnectionError(str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error uploading avatar for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")
    except Exception as e:
        logger.error(
            f"Unexpected error uploading avatar for user_id={user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to upload avatar")
