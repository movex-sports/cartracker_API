"""Renter document response contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RenterDocumentResponse(BaseModel):
    documento_id: int
    locatario_id: int
    tipo: str
    nome_original: str
    content_type: str
    documento_url: str
    created_at: datetime
    updated_at: datetime
