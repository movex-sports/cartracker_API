"""Vehicle brand and model catalog endpoints."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.database import get_connection
from app.schemas.catalog import BrandResponse, ModelResponse


router = APIRouter(prefix="/catalogo", tags=["vehicle catalog"])


@router.get("/marcas", response_model=list[BrandResponse])
def list_brands(
    _: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[dict]:
    try:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT marca_id, nome
                FROM marcas
                ORDER BY nome
                """
            ).fetchall()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o catalogo de marcas",
        ) from error


@router.get("/marcas/{marca_id}/modelos", response_model=list[ModelResponse])
def list_models(
    marca_id: int,
    _: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[dict]:
    try:
        with get_connection() as connection:
            brand_exists = connection.execute(
                "SELECT 1 FROM marcas WHERE marca_id = %(marca_id)s",
                {"marca_id": marca_id},
            ).fetchone()
            if not brand_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Marca nao encontrada",
                )

            return connection.execute(
                """
                SELECT modelo_id, marca_id, nome
                FROM modelos
                WHERE marca_id = %(marca_id)s
                ORDER BY nome
                """,
                {"marca_id": marca_id},
            ).fetchall()
    except HTTPException:
        raise
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o catalogo de modelos",
        ) from error
