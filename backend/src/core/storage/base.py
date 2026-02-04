from abc import ABC, abstractmethod
from typing import Optional
from fastapi import UploadFile


class StorageProvider(ABC):
    """Abstract base class for storage providers."""

    @abstractmethod
    async def upload_file(
        self, file: UploadFile, user_id: int, folder: str = "avatar"
    ) -> str:
        """Upload a file and return the storage key."""
        raise NotImplementedError

    @abstractmethod
    def get_file_url(self, file_key: str) -> Optional[str]:
        """Get a public URL for a stored file if available."""
        raise NotImplementedError

    @abstractmethod
    async def delete_file(self, file_key: str) -> bool:
        """Delete a stored file and return success status."""
        raise NotImplementedError

    @abstractmethod
    async def upload_bytes(
        self,
        content: bytes,
        user_id: int,
        folder: str = "thumbnails",
        filename: Optional[str] = None,
        content_type: str = "image/png",
    ) -> str:
        """Upload raw bytes and return the storage key."""
        raise NotImplementedError

    @abstractmethod
    async def download_file(self, file_key: str) -> Optional[bytes]:
        """Download file bytes by storage key, or None if not found."""
        raise NotImplementedError
