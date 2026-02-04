import boto3
import os
import asyncio
from typing import Optional
from botocore.config import Config
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import UploadFile, HTTPException
import uuid
from ..logger import SingletonLogger
from .base import StorageProvider


class SynologyStorage(StorageProvider):
    """Synology S3-compatible storage provider.

    Supports instance-based configuration with optional factory constructor and
    static helpers for pure utility operations.
    """

    ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        key_id: Optional[str] = None,
        application_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None,
        s3_client: Optional[object] = None,
    ):
        # Load from env if not provided
        self.endpoint_url = endpoint_url or os.getenv("SYNOLOGY_BUCKET_URL")
        self.key_id = key_id or os.getenv("SYNOLOGY_KEY_ID")
        self.application_key = application_key or os.getenv("SYNOLOGY_MASTER_KEY")
        self.bucket_name = bucket_name or os.getenv("SYNOLOGY_BUCKET_NAME")
        self.region_name = region_name or os.getenv("SYNOLOGY_REGION") or None

        if not all(
            [self.endpoint_url, self.key_id, self.application_key, self.bucket_name]
        ):
            raise ValueError(
                "Synology storage credentials not properly configured. "
                "Ensure SYNOLOGY_BUCKET_URL (or BUCKET_URL), SYNOLOGY_KEY_ID, "
                "SYNOLOGY_MASTER_KEY, and SYNOLOGY_BUCKET_NAME (or BUCKET_NAME) are set."
            )

        # Configure client for Synology S3 compatibility (avoid aws-chunked)
        cfg = Config(
            s3={
                "addressing_style": "path",
                "payload_signing_enabled": False,
            },
            retries={"max_attempts": 3},
            signature_version="s3",
        )

        self.endpoint_url = self.endpoint_url.rstrip("/")

        # Allow dependency injection of a preconfigured client (useful for tests)
        if s3_client is None:
            client_kwargs = {
                "endpoint_url": self.endpoint_url,
                "aws_access_key_id": self.key_id,
                "aws_secret_access_key": self.application_key,
                "config": cfg,
            }
            if self.region_name:
                client_kwargs["region_name"] = self.region_name
            self.s3_client = boto3.client("s3", **client_kwargs)
        else:
            self.s3_client = s3_client

        # Ensure bucket exists
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchBucket"}:
                raise ValueError(
                    f"Bucket '{self.bucket_name}' does not exist at {self.endpoint_url}. Create it first."
                )
            raise ValueError(f"Bucket access error: {e}")

    @classmethod
    def from_env(cls) -> "SynologyStorage":
        """Factory constructor using environment variables."""
        return cls()

    @staticmethod
    def is_allowed_content_type(content_type: str) -> bool:
        return content_type in SynologyStorage.ALLOWED_CONTENT_TYPES

    @staticmethod
    def build_key(user_id: int, folder: str, filename: str) -> str:
        return f"{user_id}/{folder}/{filename}"

    async def upload_file(
        self, file: UploadFile, user_id: int, folder: str = "avatar"
    ) -> str:
        """Upload file to Synology S3 and return the file key"""
        # Validate file type
        if not SynologyStorage.is_allowed_content_type(file.content_type):
            raise HTTPException(
                status_code=400, detail="Only JPEG and PNG files are allowed"
            )

        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Create the key path
        key = SynologyStorage.build_key(user_id, folder, unique_filename)

        try:
            # Read file content
            file_content = await file.read()

            # Upload to Synology S3 (wrap blocking boto3 call)
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentLength=len(file_content),
                ContentType=file.content_type,
            )

            return key

        except NoCredentialsError as e:
            SingletonLogger().get_logger().error(f"Storage credentials error: {e}")
            raise HTTPException(status_code=500, detail="Storage credentials error")
        except ClientError as e:
            SingletonLogger().get_logger().error(f"Storage upload error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Storage upload error: {str(e)}"
            )
        except Exception as e:
            SingletonLogger().get_logger().error(f"Upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    def get_file_url(self, file_key: str) -> Optional[str]:
        """Generate public URL for the file (if bucket/server serves it)."""
        if not file_key:
            return None
        base = (self.endpoint_url or "").rstrip("/")
        return f"{base}/{self.bucket_name}/{file_key}"

    async def delete_file(self, file_key: str) -> bool:
        """Delete file from Synology S3"""
        try:
            await asyncio.to_thread(
                self.s3_client.delete_object, Bucket=self.bucket_name, Key=file_key
            )
            return True
        except ClientError as e:
            SingletonLogger().get_logger().error(
                f"Client error deleting file {file_key}: {e}"
            )
            return False
        except Exception as e:
            SingletonLogger().get_logger().error(f"Error deleting file {file_key}: {e}")
            return False

    async def upload_bytes(
        self,
        content: bytes,
        user_id: int,
        folder: str = "thumbnails",
        filename: Optional[str] = None,
        content_type: str = "image/png",
    ) -> str:
        """Upload raw bytes to Synology S3 and return the file key.

        This is useful for programmatically generated assets (e.g., PDF thumbnails).
        """
        try:
            name = filename or f"{uuid.uuid4()}.png"
            key = f"{user_id}/{folder}/{name}"
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentLength=len(content),
                ContentType=content_type,
            )
            return key
        except NoCredentialsError as e:
            SingletonLogger().get_logger().error(f"Storage credentials error: {e}")
            raise HTTPException(status_code=500, detail="Storage credentials error")
        except ClientError as e:
            SingletonLogger().get_logger().error(f"Storage upload error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Storage upload error: {str(e)}"
            )
        except Exception as e:
            SingletonLogger().get_logger().error(f"Upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def download_file(self, file_key: str) -> Optional[bytes]:
        """Download file bytes from Synology S3."""
        try:
            response = await asyncio.to_thread(
                self.s3_client.get_object, Bucket=self.bucket_name, Key=file_key
            )
            body = response.get("Body")
            if body is None:
                return None
            # Read the stream in a thread to avoid blocking the event loop
            content = await asyncio.to_thread(body.read)
            return content
        except ClientError as e:
            SingletonLogger().get_logger().error(
                f"Client error downloading file {file_key}: {e}"
            )
            return None
        except Exception as e:
            SingletonLogger().get_logger().error(
                f"Error downloading file {file_key}: {e}"
            )
            return None

storage = SynologyStorage.from_env()