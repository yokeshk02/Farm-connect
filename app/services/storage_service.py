"""Pluggable persistent storage abstraction for FarmConnect machinery photos.

Supports:
1. LocalStorageBackend (default): local filesystem or persistent host volume.
2. S3StorageBackend: S3-compatible cloud object storage (AWS S3, Cloudflare R2, MinIO, DigitalOcean Spaces).
"""

import os
from io import BytesIO
from pathlib import Path
from flask import current_app


class StorageBackend:
    """Abstract interface for machinery media storage."""

    def save(self, file_data: BytesIO, filename: str, content_type: str) -> str:
        """Save file data and return its public web-accessible URL."""
        raise NotImplementedError

    def delete(self, file_url: str) -> bool:
        """Delete file associated with the given public URL."""
        raise NotImplementedError

    def exists(self, file_url: str) -> bool:
        """Check whether the file exists in storage."""
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """Local filesystem or persistent host volume storage backend."""

    def __init__(self, base_dir: Path | str | None = None, url_prefix: str = "/static/uploads/machinery"):
        self.base_dir = Path(base_dir) if base_dir else Path(current_app.root_path) / "static" / "uploads" / "machinery"
        self.url_prefix = url_prefix.rstrip("/")

    def save(self, file_data: BytesIO, filename: str, content_type: str) -> str:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        dest_path = self.base_dir / filename
        file_data.seek(0)
        with open(dest_path, "wb") as f:
            f.write(file_data.read())
        return f"{self.url_prefix}/{filename}"

    def delete(self, file_url: str) -> bool:
        if not file_url:
            return False
        # Extract filename from relative or absolute URL
        filename = file_url.split("/")[-1]
        target_path = self.base_dir / filename
        try:
            if target_path.exists():
                target_path.unlink()
                return True
        except Exception as e:
            current_app.logger.warning(f"LocalStorage delete error for {target_path}: {e}")
        return False

    def exists(self, file_url: str) -> bool:
        if not file_url:
            return False
        filename = file_url.split("/")[-1]
        target_path = self.base_dir / filename
        return target_path.exists()


class S3StorageBackend(StorageBackend):
    """S3-compatible object storage adapter (AWS S3, Cloudflare R2, DigitalOcean Spaces, MinIO)."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        custom_domain: str | None = None,
        prefix: str = "machinery",
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.region_name = region_name or "us-east-1"
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.custom_domain = custom_domain.rstrip("/") if custom_domain else None
        self.prefix = prefix.strip("/")

    def _get_client(self):
        try:
            import boto3
        except ImportError:
            raise RuntimeError(
                "The 'boto3' package is required for S3StorageBackend. "
                "Install it with 'pip install boto3' to activate S3 storage."
            )
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

    def save(self, file_data: BytesIO, filename: str, content_type: str) -> str:
        s3 = self._get_client()
        key = f"{self.prefix}/{filename}" if self.prefix else filename
        file_data.seek(0)
        s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_data.read(),
            ContentType=content_type,
        )
        if self.custom_domain:
            return f"{self.custom_domain}/{key}"
        elif self.endpoint_url and "supabase.co/storage/v1/s3" in self.endpoint_url:
            base_supabase = self.endpoint_url.split("/storage/v1/s3")[0]
            return f"{base_supabase}/storage/v1/object/public/{self.bucket_name}/{key}"
        elif self.endpoint_url:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{key}"
        else:
            return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"

    def delete(self, file_url: str) -> bool:
        if not file_url:
            return False
        key = file_url.split(f"/{self.prefix}/")[-1] if f"/{self.prefix}/" in file_url else file_url.split("/")[-1]
        full_key = f"{self.prefix}/{key}" if self.prefix and not key.startswith(f"{self.prefix}/") else key
        try:
            s3 = self._get_client()
            s3.delete_object(Bucket=self.bucket_name, Key=full_key)
            return True
        except Exception as e:
            current_app.logger.warning(f"S3Storage delete error for key {full_key}: {e}")
            return False

    def exists(self, file_url: str) -> bool:
        if not file_url:
            return False
        key = file_url.split(f"/{self.prefix}/")[-1] if f"/{self.prefix}/" in file_url else file_url.split("/")[-1]
        full_key = f"{self.prefix}/{key}" if self.prefix and not key.startswith(f"{self.prefix}/") else key
        try:
            s3 = self._get_client()
            s3.head_object(Bucket=self.bucket_name, Key=full_key)
            return True
        except Exception:
            return False


def get_storage_backend() -> StorageBackend:
    """Factory resolving active StorageBackend based on application configuration."""
    backend_type = (current_app.config.get("STORAGE_BACKEND") or os.getenv("STORAGE_BACKEND", "local")).lower()

    if backend_type == "s3":
        bucket = current_app.config.get("S3_BUCKET_NAME") or os.getenv("S3_BUCKET_NAME")
        if not bucket:
            raise RuntimeError("STORAGE_BACKEND=s3 requires 'S3_BUCKET_NAME' configuration.")
        return S3StorageBackend(
            bucket_name=bucket,
            endpoint_url=current_app.config.get("S3_ENDPOINT_URL") or os.getenv("S3_ENDPOINT_URL"),
            region_name=current_app.config.get("S3_REGION_NAME") or os.getenv("S3_REGION_NAME", "auto"),
            access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=current_app.config.get("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY"),
            custom_domain=current_app.config.get("S3_CUSTOM_DOMAIN") or os.getenv("S3_CUSTOM_DOMAIN"),
        )

    # Default to LocalStorageBackend
    upload_dir = Path(current_app.config.get("UPLOAD_FOLDER", Path(current_app.root_path) / "static" / "uploads")) / "machinery"
    return LocalStorageBackend(base_dir=upload_dir, url_prefix="/static/uploads/machinery")
