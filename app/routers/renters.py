"""Renter endpoints."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.database import get_connection
from app.schemas.renter import RenterCreate, RenterResponse


router = APIRouter(tags=["renters"])


@router.post(
    "/veiculos/{veiculo_id}/locatarios",
    response_model=RenterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_renter(
    payload: RenterCreate,
    veiculo_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            vehicle_exists = connection.execute(
                """
                SELECT 1
                FROM veiculos
                WHERE veiculo_id = %(veiculo_id)s
                  AND empresa_id = %(empresa_id)s
                """,
                {
                    "veiculo_id": veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not vehicle_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Veiculo nao encontrado",
                )

            renter = connection.execute(
                """
                INSERT INTO locatarios (
                    empresa_id, veiculo_id, locatario_nome,
                    locatario_sobrenome, locatario_cpf, locatario_rua,
                    locatario_numero, locatario_cep, locatario_bairro,
                    locatario_cidade, locatario_estado
                )
                VALUES (
                    %(empresa_id)s, %(veiculo_id)s, %(locatario_nome)s,
                    %(locatario_sobrenome)s, %(locatario_cpf)s,
                    %(locatario_rua)s, %(locatario_numero)s,
                    %(locatario_cep)s, %(locatario_bairro)s,
                    %(locatario_cidade)s, %(locatario_estado)s
                )
                RETURNING
                    locatario_id, empresa_id, veiculo_id, locatario_nome,
                    locatario_sobrenome, locatario_cpf, locatario_rua,
                    locatario_numero, locatario_cep, locatario_bairro,
                    locatario_cidade, locatario_estado
                """,
                {
                    **payload.model_dump(),
                    "empresa_id": current_user.empresa_id,
                    "veiculo_id": veiculo_id,
                },
            ).fetchone()
    except HTTPException:
        raise
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    return renter


@router.get("/locatarios", response_model=list[RenterResponse])
def list_renters(
    veiculo_id: int | None = Query(default=None, gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[dict]:
    try:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    locatario_id, empresa_id, veiculo_id, locatario_nome,
                    locatario_sobrenome, locatario_cpf, locatario_rua,
                    locatario_numero, locatario_cep, locatario_bairro,
                    locatario_cidade, locatario_estado
                FROM locatarios
                WHERE empresa_id = %(empresa_id)s
                  AND (
                      %(veiculo_id)s::BIGINT IS NULL
                      OR veiculo_id = %(veiculo_id)s
                  )
                ORDER BY locatario_nome, locatario_sobrenome, locatario_id
                """,
                {
                    "empresa_id": current_user.empresa_id,
                    "veiculo_id": veiculo_id,
                },
            ).fetchall()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error
