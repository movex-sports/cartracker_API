"""PostgreSQL connection helpers."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings


def get_connection() -> psycopg.Connection:
    """Open a PostgreSQL connection whose rows behave like dictionaries."""
    return psycopg.connect(
        get_settings().database_url,
        connect_timeout=10,
        row_factory=dict_row,
    )


def check_database() -> None:
    """Raise an exception when PostgreSQL is unavailable."""
    with get_connection() as connection:
        connection.execute("SELECT 1").fetchone()
