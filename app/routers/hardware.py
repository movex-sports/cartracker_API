"""Hardware endpoints."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.database import get_connection
from app.schemas.hardware import HardwareCreate, HardwareResponse


router = APIRouter(prefix="/hardware", tags=["hardware"])


@router.post("", response_model=HardwareResponse, status_code=status.HTTP_201_CREATED)
def create_hardware(
    payload: HardwareCreate,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    if payload.empresa_id != current_user.empresa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nao e permitido gerar hardware para outra empresa",
        )

    try:
        with get_connection() as connection:
            hardware = connection.execute(
                """
                INSERT INTO hardware (empresa_id)
                VALUES (%(empresa_id)s)
                RETURNING hardware_id, empresa_id
                """,
                {"empresa_id": payload.empresa_id},
            ).fetchone()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    return hardware
