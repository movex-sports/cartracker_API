"""Vehicle endpoints."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.database import get_connection
from app.schemas.vehicle import VehicleCreate, VehicleListItem, VehicleResponse


router = APIRouter(prefix="/veiculos", tags=["vehicles"])


@router.get("", response_model=list[VehicleListItem])
def list_vehicles(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[dict]:
    try:
        with get_connection() as connection:
            vehicles = connection.execute(
                """
                SELECT
                    veiculo_id, empresa_id, hardware_id, marca, modelo, ano,
                    cor, placa, combustivel_tipo, capacidade_tanque_l,
                    consumo_km_l, velocidade_maxima_kmh, odometro_km
                FROM veiculos
                WHERE empresa_id = %(empresa_id)s
                ORDER BY marca, modelo, ano DESC, veiculo_id
                """,
                {"empresa_id": current_user.empresa_id},
            ).fetchall()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    return vehicles


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            vehicle = connection.execute(
                """
                INSERT INTO veiculos (
                    empresa_id, hardware_id, marca, modelo, ano, cor, placa,
                    combustivel_tipo, capacidade_tanque_l, consumo_km_l,
                    velocidade_maxima_kmh
                )
                VALUES (
                    %(empresa_id)s, NULL, %(marca)s, %(modelo)s, %(ano)s,
                    %(cor)s, %(placa)s, %(combustivel_tipo)s,
                    %(capacidade_tanque_l)s, %(consumo_km_l)s,
                    %(velocidade_maxima_kmh)s
                )
                RETURNING
                    veiculo_id, empresa_id, hardware_id, marca, modelo, ano,
                    cor, placa, combustivel_tipo, capacidade_tanque_l,
                    consumo_km_l, velocidade_maxima_kmh
                """,
                {
                    **payload.model_dump(),
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
    except psycopg.errors.UniqueViolation as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Placa ja cadastrada",
        ) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    return vehicle
