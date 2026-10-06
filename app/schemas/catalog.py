"""Vehicle catalog response contracts."""

from __future__ import annotations

from pydantic import BaseModel


class BrandResponse(BaseModel):
    marca_id: int
    nome: str


class ModelResponse(BaseModel):
    modelo_id: int
    marca_id: int
    nome: str
