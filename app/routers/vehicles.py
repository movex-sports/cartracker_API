"""Vehicle endpoints."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.database import get_connection
from app.schemas.vehicle import VehicleCreate, VehicleListItem, VehicleResponse
from app.storage import StorageError, create_download_url


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
                    veiculo.veiculo_id, veiculo.empresa_id,
                    veiculo.hardware_id, veiculo.locatario_id,
                    veiculo.marca, veiculo.modelo, veiculo.ano,
                    veiculo.cor, veiculo.placa, veiculo.combustivel_tipo,
                    veiculo.capacidade_tanque_l, veiculo.consumo_km_l,
                    veiculo.velocidade_maxima_kmh, veiculo.odometro_km,
                    foto.object_key AS foto_thumb_object_key
                FROM veiculos AS veiculo
                LEFT JOIN fotos AS foto
                    ON foto.veiculo_id = veiculo.veiculo_id
                   AND foto.thumb = TRUE
                WHERE veiculo.empresa_id = %(empresa_id)s
                ORDER BY
                    veiculo.marca,
                    veiculo.modelo,
                    veiculo.ano DESC,
                    veiculo.veiculo_id
                """,
                {"empresa_id": current_user.empresa_id},
            ).fetchall()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    try:
        for vehicle in vehicles:
            object_key = vehicle.pop("foto_thumb_object_key")
            vehicle["foto_thumb_url"] = (
                create_download_url(object_key) if object_key else None
            )
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
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
                    veiculo_id, empresa_id, hardware_id, locatario_id,
                    marca, modelo, ano, cor, placa, combustivel_tipo,
                    capacidade_tanque_l,
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
