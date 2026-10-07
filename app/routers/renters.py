"""Renter endpoints."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.database import get_connection
from app.schemas.renter import RenterActivationRequest, RenterCreate, RenterResponse


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
                SELECT locatario_id
                FROM veiculos
                WHERE veiculo_id = %(veiculo_id)s
                  AND empresa_id = %(empresa_id)s
                FOR UPDATE
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
            if vehicle_exists["locatario_id"] is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Veiculo ja possui um locatario",
                )

            renter = connection.execute(
                """
                INSERT INTO locatarios (
                    empresa_id, locatario_nome, locatario_sobrenome,
                    locatario_cpf, locatario_rua,
                    locatario_numero, locatario_cep, locatario_bairro,
                    locatario_cidade, locatario_estado
                )
                VALUES (
                    %(empresa_id)s, %(locatario_nome)s,
                    %(locatario_sobrenome)s, %(locatario_cpf)s,
                    %(locatario_rua)s, %(locatario_numero)s,
                    %(locatario_cep)s, %(locatario_bairro)s,
                    %(locatario_cidade)s, %(locatario_estado)s
                )
                RETURNING
                    locatario_id, empresa_id, locatario_nome,
                    locatario_sobrenome, locatario_cpf, locatario_rua,
                    locatario_numero, locatario_cep, locatario_bairro,
                    locatario_cidade, locatario_estado, status
                """,
                {
                    **payload.model_dump(),
                    "empresa_id": current_user.empresa_id,
                    "veiculo_id": veiculo_id,
                },
            ).fetchone()

            connection.execute(
                """
                UPDATE veiculos
                SET locatario_id = %(locatario_id)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE veiculo_id = %(veiculo_id)s
                  AND empresa_id = %(empresa_id)s
                """,
                {
                    "locatario_id": renter["locatario_id"],
                    "veiculo_id": veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            )
            renter["veiculo_id"] = veiculo_id
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
                    locatario.locatario_id, locatario.empresa_id,
                    veiculo.veiculo_id, locatario.locatario_nome,
                    locatario.locatario_sobrenome, locatario.locatario_cpf,
                    locatario.locatario_rua, locatario.locatario_numero,
                    locatario.locatario_cep, locatario.locatario_bairro,
                    locatario.locatario_cidade, locatario.locatario_estado,
                    locatario.status
                FROM locatarios AS locatario
                LEFT JOIN veiculos AS veiculo
                    ON veiculo.locatario_id = locatario.locatario_id
                   AND veiculo.empresa_id = locatario.empresa_id
                WHERE locatario.empresa_id = %(empresa_id)s
                  AND (
                      %(veiculo_id)s::BIGINT IS NULL
                      OR veiculo.veiculo_id = %(veiculo_id)s
                  )
                ORDER BY
                    locatario.locatario_nome,
                    locatario.locatario_sobrenome,
                    locatario.locatario_id
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


@router.patch(
    "/locatarios/{locatario_id}/desativar",
    response_model=RenterResponse,
)
def deactivate_renter(
    locatario_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            renter = connection.execute(
                """
                SELECT locatario_id
                FROM locatarios
                WHERE locatario_id = %(locatario_id)s
                  AND empresa_id = %(empresa_id)s
                FOR UPDATE
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not renter:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Locatario nao encontrado",
                )

            connection.execute(
                """
                UPDATE veiculos
                SET locatario_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE locatario_id = %(locatario_id)s
                  AND empresa_id = %(empresa_id)s
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
                },
            )

            renter = connection.execute(
                """
                UPDATE locatarios
                SET status = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE locatario_id = %(locatario_id)s
                  AND empresa_id = %(empresa_id)s
                RETURNING
                    locatario_id, empresa_id, NULL::BIGINT AS veiculo_id,
                    locatario_nome, locatario_sobrenome, locatario_cpf,
                    locatario_rua, locatario_numero, locatario_cep,
                    locatario_bairro, locatario_cidade, locatario_estado,
                    status
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
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


@router.patch(
    "/locatarios/{locatario_id}/ativar",
    response_model=RenterResponse,
)
def activate_renter(
    payload: RenterActivationRequest,
    locatario_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            renter = connection.execute(
                """
                SELECT locatario_id
                FROM locatarios
                WHERE locatario_id = %(locatario_id)s
                  AND empresa_id = %(empresa_id)s
                FOR UPDATE
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not renter:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Locatario nao encontrado",
                )

            current_vehicle = connection.execute(
                """
                SELECT veiculo_id
                FROM veiculos
                WHERE locatario_id = %(locatario_id)s
                  AND empresa_id = %(empresa_id)s
                FOR UPDATE
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if current_vehicle and current_vehicle["veiculo_id"] != payload.veiculo_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Locatario ja esta atribuido a outro veiculo",
                )

            vehicle = connection.execute(
                """
                SELECT locatario_id
                FROM veiculos
                WHERE veiculo_id = %(veiculo_id)s
                  AND empresa_id = %(empresa_id)s
                FOR UPDATE
                """,
                {
                    "veiculo_id": payload.veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not vehicle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Veiculo nao encontrado",
                )
            if vehicle["locatario_id"] not in (None, locatario_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Veiculo ja possui um locatario",
                )

            connection.execute(
                """
                UPDATE locatarios
                SET status = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE locatario_id = %(locatario_id)s
                  AND empresa_id = %(empresa_id)s
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
                },
            )

            connection.execute(
                """
                UPDATE veiculos
                SET locatario_id = %(locatario_id)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE veiculo_id = %(veiculo_id)s
                  AND empresa_id = %(empresa_id)s
                """,
                {
                    "locatario_id": locatario_id,
                    "veiculo_id": payload.veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            )

            renter = connection.execute(
                """
                SELECT
                    locatario.locatario_id, locatario.empresa_id,
                    veiculo.veiculo_id, locatario.locatario_nome,
                    locatario.locatario_sobrenome, locatario.locatario_cpf,
                    locatario.locatario_rua, locatario.locatario_numero,
                    locatario.locatario_cep, locatario.locatario_bairro,
                    locatario.locatario_cidade, locatario.locatario_estado,
                    locatario.status
                FROM locatarios AS locatario
                LEFT JOIN veiculos AS veiculo
                    ON veiculo.locatario_id = locatario.locatario_id
                   AND veiculo.empresa_id = locatario.empresa_id
                WHERE locatario.locatario_id = %(locatario_id)s
                  AND locatario.empresa_id = %(empresa_id)s
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
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
