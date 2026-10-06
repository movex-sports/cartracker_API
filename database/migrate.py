"""Apply or revert the Car Tracker PostgreSQL schema migration."""

from __future__ import annotations

import argparse
from pathlib import Path

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def load_database_url() -> str:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        raise RuntimeError(f"Arquivo de configuracao nao encontrado: {env_path}")

    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if line.startswith("DATABASE_URL="):
            database_url = line.partition("=")[2].strip()
            if database_url:
                return database_url

    raise RuntimeError("DATABASE_URL nao foi definida no arquivo .env")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "direction",
        choices=("up", "down"),
        nargs="?",
        default="up",
        help="aplica (up) ou reverte (down) a migration",
    )
    args = parser.parse_args()

    migration_path = MIGRATIONS_DIR / f"001_initial_schema.{args.direction}.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with psycopg.connect(load_database_url(), connect_timeout=15) as connection:
        connection.execute(migration_sql)

        if args.direction == "up":
            rows = connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('users', 'veiculos', 'fotos')
                ORDER BY table_name
                """
            ).fetchall()
            tables = ", ".join(row[0] for row in rows)
            print(f"Migration aplicada. Tabelas confirmadas: {tables}")
        else:
            print("Migration revertida.")


if __name__ == "__main__":
    main()
