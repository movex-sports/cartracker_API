"""Backblaze B2 access through its S3-compatible API."""

from __future__ import annotations

import logging
import re
from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings


logger = logging.getLogger(__name__)


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
    upload_object(object_key, content, "image/webp", "imagem")


def upload_object(
    object_key: str,
    content: bytes,
    content_type: str,
    object_label: str = "arquivo",
) -> None:
    settings = get_settings()
    try:
        get_storage_client().put_object(
            Bucket=settings.b2_bucket_name,
            Key=object_key,
            Body=content,
            ContentType=content_type,
        )
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code", "desconhecido")
        logger.exception(
            "Backblaze recusou o upload de %s (codigo: %s, chave: %s)",
            object_label,
            error_code,
            object_key,
        )
        raise StorageError(
            f"Falha ao enviar {object_label} ao Backblaze (codigo: {error_code})"
        ) from error
    except BotoCoreError as error:
        logger.exception(
            "Falha de comunicacao no upload de %s (chave: %s)",
            object_label,
            object_key,
        )
        raise StorageError(
            f"Falha de comunicacao ao enviar {object_label} ao Backblaze"
        ) from error


def create_download_url(object_key: str, expires_in: int = 900) -> str:
    settings = get_settings()
    try:
        return get_storage_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.b2_bucket_name, "Key": object_key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as error:
        raise StorageError("Falha ao gerar URL temporaria do arquivo") from error


def delete_image(object_key: str) -> None:
    delete_object(object_key, "imagem")


def delete_object(object_key: str, object_label: str = "arquivo") -> None:
    settings = get_settings()
    try:
        client = get_storage_client()
        paginator = client.get_paginator("list_object_versions")
        versions: list[dict[str, str]] = []

        for page in paginator.paginate(
            Bucket=settings.b2_bucket_name,
            Prefix=object_key,
        ):
            for item in [*page.get("Versions", []), *page.get("DeleteMarkers", [])]:
                if item.get("Key") == object_key and item.get("VersionId"):
                    versions.append(
                        {
                            "Key": object_key,
                            "VersionId": item["VersionId"],
                        }
                    )

        for version in versions:
            client.delete_object(
                Bucket=settings.b2_bucket_name,
                Key=version["Key"],
                VersionId=version["VersionId"],
            )
    except (BotoCoreError, ClientError) as error:
        raise StorageError(
            f"Falha ao excluir permanentemente as versoes do {object_label} no Backblaze"
        ) from error
