"""Vehicle telemetry request and response contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RawDataCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    veiculo_id: int = Field(gt=0)
    ignicao: bool
    bateria: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    velocidade: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=11, decimal_places=7)
    latitude: Decimal = Field(ge=-90, le=90, max_digits=10, decimal_places=7)


class RawDataResponse(RawDataCreate):
    status_id: int
    registrado_em: datetime


class RentedVehicleLatestStatus(BaseModel):
    veiculo_id: int
    locatario_id: int
    marca: str
    modelo: str
    placa: str
    status_id: int | None
    ignicao: bool | None
    bateria: Decimal | None
    velocidade: Decimal | None
    longitude: Decimal | None
    latitude: Decimal | None
    registrado_em: datetime | None
