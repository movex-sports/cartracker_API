"""PostgreSQL connection helpers."""

from __future__ import annotations

import psycopg

from app.config import get_settings


def check_database() -> None:
    """Raise an exception when PostgreSQL is unavailable."""
    with psycopg.connect(get_settings().database_url, connect_timeout=10) as connection:
        connection.execute("SELECT 1").fetchone()
