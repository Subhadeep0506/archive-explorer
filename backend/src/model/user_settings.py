from typing import TYPE_CHECKING, Dict
import os
import json
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from cryptography.fernet import Fernet
from ..database.db import Base, TimestampMixin


ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is not set")

fernet = Fernet(ENCRYPTION_KEY.encode())


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    custom_summary_instructions: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    usability_analysis_instructions: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    summary_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    usability_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    api_keys_encrypted: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    if TYPE_CHECKING:
        from .user import User  # pragma: no cover

    user: Mapped["User"] = relationship("User", back_populates="user_settings")

    @property
    def api_keys(self) -> list[dict] | None:
        """
        Decrypt and return API keys as a list of dictionaries.
        Each dict contains: {id, slug, name, api_key}

        SECURITY WARNING: This property decrypts all API keys and should NEVER
        be used when returning data to the frontend. Use api_keys_encrypted instead.
        Only use this property internally when you need to access decrypted keys
        for making actual API requests to external services.
        """
        if self.api_keys_encrypted:
            try:
                # If it's already a list (stored in JSONB), decrypt each api_key
                if isinstance(self.api_keys_encrypted, list):
                    decrypted_list = []
                    for item in self.api_keys_encrypted:
                        decrypted_item = item.copy()
                        if "api_key" in decrypted_item and decrypted_item["api_key"]:
                            decrypted_item["api_key"] = fernet.decrypt(
                                decrypted_item["api_key"].encode()
                            ).decode()
                        decrypted_list.append(decrypted_item)
                    return decrypted_list
                # Legacy support: if it's a string, try to decrypt and parse
                elif isinstance(self.api_keys_encrypted, str):
                    decrypted = fernet.decrypt(
                        self.api_keys_encrypted.encode()
                    ).decode()
                    return json.loads(decrypted)
            except Exception as e:
                # Handle decryption errors, perhaps log and return None
                return None
        return None

    @api_keys.setter
    def api_keys(self, value: list[dict] | None):
        """
        Encrypt and set API keys from a list of dictionaries.
        Each dict should contain: {id, slug, name, api_key}
        """
        if value:
            try:
                # Encrypt only the api_key field in each dictionary
                encrypted_list = []
                for item in value:
                    encrypted_item = item.copy()
                    if "api_key" in encrypted_item and encrypted_item["api_key"]:
                        encrypted_item["api_key"] = fernet.encrypt(
                            encrypted_item["api_key"].encode()
                        ).decode()
                    encrypted_list.append(encrypted_item)
                self.api_keys_encrypted = encrypted_list
            except Exception as e:
                # Handle encryption errors
                self.api_keys_encrypted = None
        else:
            self.api_keys_encrypted = None

    @property
    def available_api_keys(self) -> list[str] | None:
        """Return the list of available API key slugs."""
        keys = self.api_keys
        if keys:
            return [item.get("slug") for item in keys if "slug" in item]
        return None

    def get_api_key(self, service_slug: str) -> str | None:
        """
        Get API key for a specific service by its slug.

        SECURITY NOTE: This method decrypts the API key and should ONLY be used
        when actually making API requests to external services. Never use this
        method when returning data to the frontend - use api_keys_encrypted instead.

        Args:
            service_slug: The slug of the service from ServiceCatalog (e.g., 'tavily', 'groq')

        Returns:
            The decrypted API key string if found, None otherwise
        """
        keys = self.api_keys
        if keys:
            for item in keys:
                if item.get("slug") == service_slug:
                    return item.get("api_key")
        return None

    def set_api_key(
        self, service_id: int, service_slug: str, service_name: str, api_key: str
    ) -> None:
        """
        Set or update API key for a specific service.

        Args:
            service_id: The ID of the service from ServiceCatalog
            service_slug: The slug of the service from ServiceCatalog
            service_name: The name of the service
            api_key: The API key value to store (will be encrypted)
        """
        keys = self.api_keys or []

        # Check if service already exists, update it
        found = False
        for item in keys:
            if item.get("slug") == service_slug:
                item["api_key"] = api_key
                item["id"] = service_id
                item["name"] = service_name
                found = True
                break

        # If not found, add new entry
        if not found:
            keys.append(
                {
                    "id": service_id,
                    "slug": service_slug,
                    "name": service_name,
                    "api_key": api_key,
                }
            )

        self.api_keys = keys  # This triggers the setter which encrypts

    def remove_api_key(self, service_slug: str) -> bool:
        """
        Remove API key for a specific service.

        Args:
            service_slug: The slug of the service from ServiceCatalog

        Returns:
            True if the key was removed, False if it didn't exist
        """
        keys = self.api_keys
        if keys:
            original_length = len(keys)
            keys = [item for item in keys if item.get("slug") != service_slug]
            if len(keys) < original_length:
                self.api_keys = keys  # This triggers the setter which encrypts
                return True
        return False

    def __repr__(self) -> str:
        return f"UserSettings(id={self.id}, user_id={self.user_id})"
