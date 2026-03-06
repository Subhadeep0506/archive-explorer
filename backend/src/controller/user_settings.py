"""
Controller for user settings operations.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import UserSettings
from src.schema.user_settings import UserSettingsUpdate
from fastapi import HTTPException, status


class UserSettingsController:
    """Controller for user settings operations."""

    @staticmethod
    async def get_user_settings(
        session: AsyncSession, user_id: int
    ) -> Optional[UserSettings]:
        """
        Get user settings by user ID.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            UserSettings object or None if not found
        """
        result = await session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user_settings(
        session: AsyncSession,
        user_id: int,
        location: Optional[str] = None,
        custom_summary_instructions: Optional[str] = None,
        usability_analysis_instructions: Optional[str] = None,
        api_keys: Optional[list[dict]] = None,
    ) -> UserSettings:
        """
        Create user settings.

        Args:
            session: Database session
            user_id: User ID
            location: User location
            custom_summary_instructions: Custom summary instructions
            usability_analysis_instructions: Usability analysis instructions
            api_keys: List of API key dictionaries

        Returns:
            Created UserSettings object
        """
        settings = UserSettings(
            user_id=user_id,
            location=location,
            custom_summary_instructions=custom_summary_instructions,
            usability_analysis_instructions=usability_analysis_instructions,
        )

        if api_keys:
            settings.api_keys = api_keys

        session.add(settings)
        await session.commit()
        await session.refresh(settings)
        return settings

    @staticmethod
    async def update_user_settings(
        session: AsyncSession, user_id: int, settings_data: UserSettingsUpdate
    ) -> UserSettings:
        """
        Update user settings.

        Args:
            session: Database session
            user_id: User ID
            settings_data: Settings data to update

        Returns:
            Updated UserSettings object

        Raises:
            HTTPException: If settings not found
        """
        # Get existing settings
        settings = await UserSettingsController.get_user_settings(session, user_id)

        if not settings:
            # Create new settings if they don't exist
            api_keys = None
            if settings_data.api_keys_encrypted:
                api_keys = [
                    item.model_dump() for item in settings_data.api_keys_encrypted
                ]

            settings = await UserSettingsController.create_user_settings(
                session=session,
                user_id=user_id,
                location=settings_data.location,
                custom_summary_instructions=settings_data.custom_summary_instructions,
                usability_analysis_instructions=settings_data.usability_analysis_instructions,
                api_keys=api_keys,
            )
            return settings

        # Update existing settings
        update_data = settings_data.model_dump(exclude_unset=True)

        # Handle api_keys_encrypted separately
        if "api_keys_encrypted" in update_data:
            api_keys = update_data.pop("api_keys_encrypted")
            if api_keys is not None:
                # Convert Pydantic models to dicts
                settings.api_keys = [
                    item.model_dump() if hasattr(item, "model_dump") else item
                    for item in api_keys
                ]

        # Update other fields
        for field, value in update_data.items():
            setattr(settings, field, value)

        await session.commit()
        await session.refresh(settings)
        return settings

    @staticmethod
    async def get_or_create_user_settings(
        session: AsyncSession, user_id: int
    ) -> UserSettings:
        """
        Get user settings, creating them if they don't exist.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            UserSettings object
        """
        settings = await UserSettingsController.get_user_settings(session, user_id)

        if not settings:
            settings = await UserSettingsController.create_user_settings(
                session, user_id
            )

        return settings
