"""
Controller for user settings operations.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import UserSettings
from src.schema.user_settings import UserSettingsUpdate
from fastapi import HTTPException, status
from cryptography.fernet import Fernet, InvalidToken
import os

# Get the same encryption key used by the model
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is not set")

fernet = Fernet(ENCRYPTION_KEY.encode())


class UserSettingsController:
    """Controller for user settings operations."""

    @staticmethod
    def is_api_key_encrypted(api_key: str) -> bool:
        """
        Check if an API key is already encrypted (Fernet token) or plaintext.

        Args:
            api_key: The API key string to check

        Returns:
            True if encrypted, False if plaintext
        """
        if not api_key:
            return False
        if len(api_key) < 80:
            return False
        try:
            decrypted = fernet.decrypt(api_key.encode()).decode()
            return True
        except (InvalidToken, Exception) as e:
            return False

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
            # Process each key: encrypt only if not already encrypted
            processed_keys = []
            for key_item in api_keys:
                processed_item = key_item.copy()
                api_key_value = processed_item.get("api_key", "")
                slug = processed_item.get("slug", "unknown")

                # Only encrypt if the key is plaintext
                if api_key_value and not UserSettingsController.is_api_key_encrypted(
                    api_key_value
                ):
                    encrypted_value = fernet.encrypt(api_key_value.encode()).decode()
                    processed_item["api_key"] = encrypted_value
                processed_keys.append(processed_item)

            settings.api_keys_encrypted = processed_keys

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
                # Handle empty array to clear all keys
                if len(api_keys) == 0:
                    settings.api_keys_encrypted = []
                else:
                    # Process each key: encrypt only if not already encrypted
                    processed_keys = []
                    for item in api_keys:
                        key_dict = (
                            item.model_dump() if hasattr(item, "model_dump") else item
                        )
                        processed_item = key_dict.copy()
                        api_key_value = processed_item.get("api_key", "")
                        slug = processed_item.get("slug", "unknown")

                        if (
                            api_key_value
                            and not UserSettingsController.is_api_key_encrypted(
                                api_key_value
                            )
                        ):
                            encrypted_value = fernet.encrypt(
                                api_key_value.encode()
                            ).decode()
                            processed_item["api_key"] = encrypted_value

                        processed_keys.append(processed_item)

                    settings.api_keys_encrypted = processed_keys

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
