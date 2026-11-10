"""Daily vehicle route response contracts."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class RouteSummary(BaseModel):
    numero_rota: int
    primeiro_ponto_em: datetime
    ultimo_ponto_em: datetime
    quantidade_pontos: int
    em_andamento: bool


class RouteDayResponse(BaseModel):
    veiculo_id: int
    data: date
    total_rotas: int
    rotas: list[RouteSummary]


class RoutePoint(BaseModel):
    status_id: int
    latitude: Decimal
    longitude: Decimal
    velocidade: Decimal
    capturado_em: datetime


class RouteDetailResponse(BaseModel):
    veiculo_id: int
    data: date
    numero_rota: int
    em_andamento: bool
    pontos: list[RoutePoint]
