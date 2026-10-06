"""Apply or revert the Car Tracker PostgreSQL schema migrations."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def load_database_url() -> str:
    environment_url = os.getenv("DATABASE_URL")
    if environment_url:
        return environment_url

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

    with psycopg.connect(load_database_url(), connect_timeout=15) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        if args.direction == "up":
            applied_count = 0
            for migration_path in sorted(MIGRATIONS_DIR.glob("*.up.sql")):
                version = migration_path.name.removesuffix(".up.sql")
                migration_sql = migration_path.read_text(encoding="utf-8")
                checksum = hashlib.sha256(migration_sql.encode("utf-8")).hexdigest()

                applied = connection.execute(
                    "SELECT checksum FROM schema_migrations WHERE version = %s",
                    (version,),
                ).fetchone()

                if applied:
                    if applied[0] != checksum:
                        raise RuntimeError(
                            f"A migration {version} ja foi aplicada, mas foi alterada."
                        )
                    continue

                connection.execute(migration_sql)
                connection.execute(
                    "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                    (version, checksum),
                )
                applied_count += 1

            if applied_count == 0:
                print("Todas as migrations ja estavam aplicadas.")
            else:
                print(f"Migrations aplicadas: {applied_count}.")

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
            print(f"Tabelas confirmadas: {tables}")
        else:
            applied = connection.execute(
                """
                SELECT version
                FROM schema_migrations
                ORDER BY version DESC
                """
            ).fetchall()

            for (version,) in applied:
                migration_path = MIGRATIONS_DIR / f"{version}.down.sql"
                if not migration_path.exists():
                    raise RuntimeError(f"Rollback ausente para {version}")
                connection.execute(migration_path.read_text(encoding="utf-8"))
                connection.execute(
                    "DELETE FROM schema_migrations WHERE version = %s",
                    (version,),
                )

            print(f"Migrations revertidas: {len(applied)}.")


if __name__ == "__main__":
    main()
