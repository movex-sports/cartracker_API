"""Vehicle photo response contracts."""

from __future__ import annotations

from pydantic import BaseModel


class VehiclePhotoResponse(BaseModel):
    foto_id: int
    veiculo_id: int
    foto_url: str
    thumb: bool
