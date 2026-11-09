"""Vehicle telemetry request and response contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RawDataCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    imei: str = Field(pattern=r"^[0-9]{14,16}$")
    data_hora: datetime
    velocidade: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=11, decimal_places=7)
    latitude: Decimal = Field(ge=-90, le=90, max_digits=10, decimal_places=7)

    @field_validator("data_hora")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("data_hora deve informar o fuso horario, por exemplo Z para UTC")
        return value.astimezone(timezone.utc)


class RawDataResponse(BaseModel):
    status_id: int
    hardware_id: int
    veiculo_id: int
    ignicao: bool | None
    bateria: Decimal | None
    velocidade: Decimal
    longitude: Decimal
    latitude: Decimal
    data_hora: datetime
    registrado_em: datetime


class RentedVehicleLatestStatus(BaseModel):
    veiculo_id: int
    locatario_id: int
    locatario_nome: str
    locatario_sobrenome: str
    locatario_cpf: str
    marca: str
    modelo: str
    placa: str
    foto_thumb_url: str | None
    status_id: int | None
    ignicao: bool | None
    bateria: Decimal | None
    velocidade: Decimal | None
    longitude: Decimal | None
    latitude: Decimal | None
    coordenadas: str | None
    data_hora: datetime | None
    registrado_em: datetime | None
