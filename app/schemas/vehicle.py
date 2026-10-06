"""Vehicle request and response contracts."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FuelType(str, Enum):
    GASOLINA = "gasolina"
    ETANOL = "etanol"
    FLEX = "flex"
    DIESEL = "diesel"
    ELETRICO = "eletrico"
    HIBRIDO = "hibrido"
    GNV = "gnv"


class VehicleCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    marca: str = Field(min_length=1, max_length=80)
    modelo: str = Field(min_length=1, max_length=100)
    ano: int
    cor: str = Field(min_length=1, max_length=50)
    placa: str
    combustivel_tipo: FuelType
    capacidade_tanque_l: Decimal = Field(gt=0, max_digits=7, decimal_places=2)
    consumo_km_l: Decimal = Field(gt=0, max_digits=7, decimal_places=2)
    velocidade_maxima_kmh: Decimal = Field(gt=0, max_digits=7, decimal_places=2)

    @field_validator("ano")
    @classmethod
    def validate_ano(cls, value: int) -> int:
        max_year = datetime.now(timezone.utc).year + 1
        if not 1886 <= value <= max_year:
            raise ValueError(f"Ano deve estar entre 1886 e {max_year}")
        return value

    @field_validator("placa")
    @classmethod
    def normalize_placa(cls, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]", "", value).upper()
        if not re.fullmatch(r"[A-Z0-9]{7}", normalized):
            raise ValueError("Placa deve conter sete caracteres alfanumericos")
        return normalized

    @field_validator("combustivel_tipo", mode="before")
    @classmethod
    def normalize_fuel_type(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

class VehicleResponse(VehicleCreate):
    veiculo_id: int
    empresa_id: int
    hardware_id: int | None


class VehicleListItem(VehicleResponse):
    odometro_km: Decimal
