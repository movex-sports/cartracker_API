"""Application configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_local_env() -> None:
    """Load a local .env without overriding variables provided by Render."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


class Settings(BaseModel):
    app_name: str = "Car Tracker API"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str
    jwt_secret: str
    access_token_minutes: int = 10
    b2_endpoint: str | None = None
    b2_region: str | None = None
    b2_bucket_name: str | None = None
    b2_key_id: str | None = None
    b2_application_key: str | None = None
    b2_object_prefix: str = "fotos_veiculares"


@lru_cache
def get_settings() -> Settings:
    load_local_env()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("A variavel DATABASE_URL e obrigatoria")

    environment = os.getenv("ENVIRONMENT", "development")
    is_hosted_on_render = os.getenv("RENDER", "").lower() == "true"
    jwt_secret = os.getenv("JWT_SECRET", "")
    if (environment == "production" or is_hosted_on_render) and len(jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET deve ter pelo menos 32 caracteres em producao")
    if not jwt_secret:
        jwt_secret = "development-only-secret-change-before-production"

    return Settings(
        environment=environment,
        database_url=database_url,
        jwt_secret=jwt_secret,
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "10")),
        b2_endpoint=os.getenv("B2_ENDPOINT"),
        b2_region=os.getenv("B2_REGION"),
        b2_bucket_name=os.getenv("B2_BUCKET_NAME"),
        b2_key_id=os.getenv("B2_KEY_ID"),
        b2_application_key=os.getenv("B2_APPLICATION_KEY"),
        b2_object_prefix=os.getenv("B2_OBJECT_PREFIX", "fotos_veiculares").strip("/"),
    )
