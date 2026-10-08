"""Backblaze B2 access through its S3-compatible API."""

from __future__ import annotations

import re
from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings


class StorageError(RuntimeError):
    """Raised when the object storage configuration or operation fails."""


def infer_region(endpoint: str) -> str | None:
    match = re.search(r"https?://s3\.([^.]+)\.backblazeb2\.com", endpoint)
    return match.group(1) if match else None


@lru_cache
def get_storage_client() -> BaseClient:
    settings = get_settings()
    required = {
        "B2_ENDPOINT": settings.b2_endpoint,
        "B2_BUCKET_NAME": settings.b2_bucket_name,
        "B2_KEY_ID": settings.b2_key_id,
        "B2_APPLICATION_KEY": settings.b2_application_key,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise StorageError(f"Configuracao ausente: {', '.join(missing)}")

    region = settings.b2_region or infer_region(settings.b2_endpoint)
    return boto3.client(
        "s3",
        endpoint_url=settings.b2_endpoint,
        region_name=region,
        aws_access_key_id=settings.b2_key_id,
        aws_secret_access_key=settings.b2_application_key,
        config=Config(signature_version="s3v4"),
    )


def upload_image(object_key: str, content: bytes) -> None:
    settings = get_settings()
    try:
        get_storage_client().put_object(
            Bucket=settings.b2_bucket_name,
            Key=object_key,
            Body=content,
            ContentType="image/webp",
        )
    except (BotoCoreError, ClientError) as error:
        raise StorageError("Falha ao enviar imagem ao Backblaze") from error


def create_download_url(object_key: str, expires_in: int = 900) -> str:
    settings = get_settings()
    try:
        return get_storage_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.b2_bucket_name, "Key": object_key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as error:
        raise StorageError("Falha ao gerar URL da imagem") from error


def delete_image(object_key: str) -> None:
    settings = get_settings()
    try:
        get_storage_client().delete_object(
            Bucket=settings.b2_bucket_name,
            Key=object_key,
        )
    except (BotoCoreError, ClientError) as error:
        raise StorageError("Falha ao excluir imagem do Backblaze") from error
