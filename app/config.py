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


@lru_cache
def get_settings() -> Settings:
    load_local_env()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("A variavel DATABASE_URL e obrigatoria")

    return Settings(
        environment=os.getenv("ENVIRONMENT", "development"),
        database_url=database_url,
    )
