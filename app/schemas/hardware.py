"""Hardware request and response contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HardwareCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: int = Field(gt=0)
    imei: str | None = None

    @field_validator("imei")
    @classmethod
    def validate_imei(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized.isdigit() or not 14 <= len(normalized) <= 16:
            raise ValueError("IMEI deve conter entre 14 e 16 digitos")
        return normalized


class HardwareResponse(BaseModel):
    hardware_id: int
    empresa_id: int
    imei: str | None
    status: bool
