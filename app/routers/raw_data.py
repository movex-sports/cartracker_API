"""Hardware ingestion and latest vehicle telemetry endpoints."""

from __future__ import annotations

import secrets

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.config import get_settings
from app.database import get_connection
from app.schemas.raw_data import (
    RawDataCreate,
    RawDataResponse,
    RentedVehicleLatestStatus,
)
from app.storage import StorageError, create_download_url


router = APIRouter(prefix="/dados-crus", tags=["vehicle telemetry"])
hardware_key_header = APIKeyHeader(name="X-Hardware-Key", auto_error=False)


def decimal_to_dms(value: float, positive: str, negative: str) -> str:
    hemisphere = positive if value >= 0 else negative
    absolute = abs(value)
    degrees = int(absolute)
    minutes_total = (absolute - degrees) * 60
    minutes = int(minutes_total)
    seconds = round((minutes_total - minutes) * 60, 1)

    if seconds >= 60:
        seconds = 0.0
        minutes += 1
    if minutes >= 60:
        minutes = 0
        degrees += 1

    return f'{degrees}°{minutes:02d}\'{seconds:04.1f}"{hemisphere}'


def format_coordinates(latitude: object, longitude: object) -> str | None:
    if latitude is None or longitude is None:
        return None
    return " ".join(
        (
            decimal_to_dms(float(latitude), "N", "S"),
            decimal_to_dms(float(longitude), "E", "W"),
        )
    )


def require_hardware_key(
    provided_key: str | None = Security(hardware_key_header),
) -> None:
    expected_key = get_settings().hardware_ingest_key
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HARDWARE_INGEST_KEY nao configurada",
        )
    if not provided_key or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave do hardware invalida",
        )


def insert_raw_data(connection: psycopg.Connection, payload: RawDataCreate) -> dict:
    return connection.execute(
        """
        INSERT INTO dados_crus (
            veiculo_id, ignicao, bateria, velocidade,
            longitude, latitude
        )
        VALUES (
            %(veiculo_id)s, %(ignicao)s, %(bateria)s,
            %(velocidade)s, %(longitude)s, %(latitude)s
        )
        RETURNING
            status_id, veiculo_id, ignicao, bateria, velocidade,
            longitude, latitude, registrado_em
        """,
        payload.model_dump(),
    ).fetchone()


@router.post("", response_model=RawDataResponse, status_code=status.HTTP_201_CREATED)
def ingest_raw_data(
    payload: RawDataCreate,
    _: None = Depends(require_hardware_key),
) -> dict:
    try:
        with get_connection() as connection:
            vehicle = connection.execute(
                """
                SELECT veiculo_id, hardware_id
                FROM veiculos
                WHERE veiculo_id = %(veiculo_id)s
                """,
                {"veiculo_id": payload.veiculo_id},
            ).fetchone()
            if not vehicle:
                raise HTTPException(status_code=404, detail="Veiculo nao encontrado")
            if vehicle["hardware_id"] is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Veiculo nao possui hardware vinculado",
                )

            raw_data = insert_raw_data(connection, payload)
    except HTTPException:
        raise
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel salvar os dados do hardware",
        ) from error

    return raw_data


@router.post(
    "/manual",
    response_model=RawDataResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_raw_data(
    payload: RawDataCreate,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            vehicle = connection.execute(
                """
                SELECT veiculo_id
                FROM veiculos
                WHERE veiculo_id = %(veiculo_id)s
                  AND empresa_id = %(empresa_id)s
                """,
                {
                    "veiculo_id": payload.veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not vehicle:
                raise HTTPException(status_code=404, detail="Veiculo nao encontrado")

            raw_data = insert_raw_data(connection, payload)
    except HTTPException:
        raise
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel salvar os dados manuais",
        ) from error

    return raw_data


@router.get(
    "/veiculos-alugados",
    response_model=list[RentedVehicleLatestStatus],
)
def list_rented_vehicles_latest_status(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[dict]:
    try:
        with get_connection() as connection:
            vehicles = connection.execute(
                """
                SELECT
                    veiculo.veiculo_id, veiculo.locatario_id,
                    veiculo.marca, veiculo.modelo, veiculo.placa,
                    foto.object_key AS foto_thumb_object_key,
                    ultimo.status_id, ultimo.ignicao, ultimo.bateria,
                    ultimo.velocidade, ultimo.longitude, ultimo.latitude,
                    ultimo.registrado_em
                FROM veiculos AS veiculo
                LEFT JOIN LATERAL (
                    SELECT
                        dado.status_id, dado.ignicao, dado.bateria,
                        dado.velocidade, dado.longitude, dado.latitude,
                        dado.registrado_em
                    FROM dados_crus AS dado
                    WHERE dado.veiculo_id = veiculo.veiculo_id
                    ORDER BY dado.registrado_em DESC, dado.status_id DESC
                    LIMIT 1
                ) AS ultimo ON TRUE
                LEFT JOIN fotos AS foto
                    ON foto.veiculo_id = veiculo.veiculo_id
                   AND foto.thumb = TRUE
                WHERE veiculo.empresa_id = %(empresa_id)s
                  AND veiculo.locatario_id IS NOT NULL
                ORDER BY veiculo.marca, veiculo.modelo, veiculo.veiculo_id
                """,
                {"empresa_id": current_user.empresa_id},
            ).fetchall()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel consultar os dados dos veiculos",
        ) from error

    for vehicle in vehicles:
        vehicle["coordenadas"] = format_coordinates(
            vehicle["latitude"], vehicle["longitude"]
        )
        object_key = vehicle.pop("foto_thumb_object_key")
        try:
            vehicle["foto_thumb_url"] = (
                create_download_url(object_key) if object_key else None
            )
        except StorageError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(error),
            ) from error
    return vehicles
