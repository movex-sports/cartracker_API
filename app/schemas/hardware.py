"""Hardware request and response contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HardwareCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: int = Field(gt=0)


class HardwareResponse(BaseModel):
    hardware_id: int
    empresa_id: int
