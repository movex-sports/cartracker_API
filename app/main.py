"""HTTP entry point for the Car Tracker API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import psycopg
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import check_database
from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.hardware import router as hardware_router
from app.routers.photos import router as photos_router
from app.routers.renter_documents import router as renter_documents_router
from app.routers.renters import router as renters_router
from app.routers.raw_data import router as raw_data_router
from app.routers.users import router as users_router
from app.routers.vehicles import router as vehicles_router


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cartracker-4d0f.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(hardware_router)
app.include_router(photos_router)
app.include_router(renter_documents_router)
app.include_router(renters_router)
app.include_router(raw_data_router)
app.include_router(users_router)
app.include_router(vehicles_router)


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
