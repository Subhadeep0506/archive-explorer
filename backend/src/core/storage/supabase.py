import boto3
import os
import requests
import asyncio
from typing import Optional
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import UploadFile, HTTPException
import uuid
from ..logger import SingletonLogger
from .base import StorageProvider


class SupabaseStorage(StorageProvider):
    ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        key_id: Optional[str] = None,
        application_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None,
        service_role_key: Optional[str] = None,
        supabase_api_key: Optional[str] = None,
        s3_client: Optional[object] = None,
    ):
        # Load from env if not provided
        self.endpoint_url = endpoint_url or os.getenv("S3_STORAGE_URL")
        self.key_id = key_id or os.getenv("S3_ACCESS_KEY_ID")
        self.application_key = application_key or os.getenv("S3_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or os.getenv("S3_STORAGE_BUCKET_NAME")
        self.region_name = region_name or os.getenv("S3_STORAGE_REGION")
        self.service_role_key = service_role_key or os.getenv(
            "SUPABASE_SERVICE_ROLE_KEY"
        )
        self.supabase_api_key = supabase_api_key or os.getenv("SUPABASE_API_KEY")

        if not all(
            [self.endpoint_url, self.key_id, self.application_key, self.bucket_name]
        ):
            raise ValueError(
                "Supabase storage credentials not properly configured. "
                "Make sure S3_STORAGE_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, "
                "and S3_STORAGE_BUCKET_NAME are set in your .env file."
            )

        # Extract project reference for REST API calls
        self.project_ref = self.endpoint_url.split(".")[0].replace("https://", "")

        # Allow dependency injection of a preconfigured client
        if s3_client is None:
            client_kwargs = {
                "endpoint_url": self.endpoint_url,
                "aws_access_key_id": self.key_id,
                "aws_secret_access_key": self.application_key,
            }
            if self.region_name:
                client_kwargs["region_name"] = self.region_name
            self.s3_client = boto3.client("s3", **client_kwargs)
        else:
            self.s3_client = s3_client

        # Ensure bucket exists and is public
        self._ensure_bucket_exists_and_public()

    def _ensure_bucket_exists_and_public(self):
        """Check if bucket exists and make it public if needed"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404" or error_code == "NoSuchBucket":
                raise ValueError(
                    f"Bucket '{self.bucket_name}' does not exist. "
                    "Please create it in your Supabase dashboard under Storage first."
                )
            else:
                raise ValueError(f"Bucket access error: {e}")

        # Try to make the bucket public using Supabase REST API
        self._make_bucket_public()

    def _make_bucket_public(self):
        """Make bucket public using Supabase REST API"""
        if not self.service_role_key or not self.supabase_api_key:
            SingletonLogger().get_logger().warning(
                "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_API_KEY not found. Bucket may not be public."
            )
            SingletonLogger().get_logger().warning(
                "Please ensure the bucket is set to public in your Supabase dashboard."
            )
            return

        try:
            url = f"https://{self.project_ref}.supabase.co/storage/v1/bucket/{self.bucket_name}"
            headers = {
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json",
            }
            data = {"name": self.bucket_name, "public": True}

            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 200:
                SingletonLogger().get_logger().info(
                    f"Successfully made bucket '{self.bucket_name}' public"
                )
            else:
                SingletonLogger().get_logger().warning(
                    f"Could not make bucket public. Status: {response.status_code}"
                )
                SingletonLogger().get_logger().debug(f"Response: {response.text}")
                SingletonLogger().get_logger().warning(
                    "Please ensure the bucket is set to public in your Supabase dashboard."
                )
        except Exception as e:
            SingletonLogger().get_logger().warning(f"Error making bucket public: {e}")
            SingletonLogger().get_logger().warning(
                "Please ensure the bucket is set to public in your Supabase dashboard."
            )

    async def upload_file(
        self, file: UploadFile, user_id: int, folder: str = "avatar"
    ) -> str:
        """Upload file to Supabase Storage and return the file key"""
        # Validate file type
        if not SupabaseStorage.is_allowed_content_type(file.content_type):
            raise HTTPException(
                status_code=400, detail="Only JPEG and PNG files are allowed"
            )

        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Create the key path
        key = SupabaseStorage.build_key(user_id, folder, unique_filename)

        try:
            # Read file content
            file_content = await file.read()

            # Upload to Supabase Storage (wrap blocking boto3 call)
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
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
        """Generate public URL for the file"""
        if not file_key:
            return None

        # Extract project ref from endpoint URL
        # S3_STORAGE_URL format: https://<project_ref>.storage.supabase.co/storage/v1/s3
        project_ref = self.endpoint_url.split(".")[0].replace("https://", "")

        # Supabase Storage public URL format: https://<project_ref>.supabase.co/storage/v1/object/public/<bucket>/<file_key>
        return f"https://{project_ref}.supabase.co/storage/v1/object/public/{self.bucket_name}/{file_key}"

    async def delete_file(self, file_key: str) -> bool:
        """Delete file from Supabase Storage"""
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
        """Upload raw bytes to Supabase Storage and return the file key.

        This is useful for programmatically generated assets (e.g., PDF thumbnails).
        """
        try:
            name = filename or f"{uuid.uuid4()}.png"
            key = SupabaseStorage.build_key(user_id, folder, name)
            # Upload via S3-compatible API
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type,
                ACL="public-read",
            )
            SingletonLogger().get_logger().info(
                f"Uploaded thumbnail to storage: bucket={self.bucket_name} key={key} bytes={len(content)}"
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

    @classmethod
    def from_env(cls) -> "SupabaseStorage":
        """Factory constructor using environment variables."""
        return cls()

    @staticmethod
    def is_allowed_content_type(content_type: str) -> bool:
        return content_type in SupabaseStorage.ALLOWED_CONTENT_TYPES

    @staticmethod
    def build_key(user_id: int, folder: str, filename: str) -> str:
        return f"{user_id}/{folder}/{filename}"

    async def download_file(self, file_key: str) -> Optional[bytes]:
        """Download file bytes from Supabase Storage."""
        try:
            response = await asyncio.to_thread(
                self.s3_client.get_object, Bucket=self.bucket_name, Key=file_key
            )
            body = response.get("Body")
            if body is None:
                return None
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

    async def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in Supabase Storage bucket via HEAD."""
        try:
            await asyncio.to_thread(
                self.s3_client.head_object, Bucket=self.bucket_name, Key=file_key
            )
            return True
        except ClientError as e:
            # Not found codes vary by provider; treat 404/NoSuchKey as missing
            code = e.response.get("Error", {}).get("Code")
            if code in ("404", "NotFound", "NoSuchKey"):
                return False
            SingletonLogger().get_logger().error(
                f"Error checking existence for {file_key}: {e}"
            )
            return False
        except Exception as e:
            SingletonLogger().get_logger().error(
                f"Unexpected error checking existence for {file_key}: {e}"
            )
            return False


# Global storage instance
storage = SupabaseStorage.from_env()
