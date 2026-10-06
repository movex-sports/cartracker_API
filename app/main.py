"""HTTP entry point for the Car Tracker API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import psycopg
from fastapi import FastAPI, HTTPException, status

from app.config import get_settings
from app.database import check_database


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    check_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "online",
    }


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    try:
        check_database()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco de dados indisponivel",
        ) from error

    return {"api": "ok", "database": "ok"}
