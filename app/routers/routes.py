"""Daily vehicle route query endpoints."""

from __future__ import annotations

from datetime import date

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.database import get_connection
from app.schemas.route import RouteDayResponse, RouteDetailResponse


router = APIRouter(prefix="/veiculos/{veiculo_id}/rotas", tags=["vehicle routes"])


def require_company_vehicle(
    connection: psycopg.Connection,
    veiculo_id: int,
    empresa_id: int,
) -> None:
    vehicle = connection.execute(
        """
        SELECT 1
        FROM veiculos
        WHERE veiculo_id = %(veiculo_id)s
          AND empresa_id = %(empresa_id)s
        """,
        {"veiculo_id": veiculo_id, "empresa_id": empresa_id},
    ).fetchone()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veiculo nao encontrado")


@router.get("", response_model=RouteDayResponse)
def list_vehicle_routes(
    veiculo_id: int = Path(gt=0),
    data: date = Query(),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            require_company_vehicle(connection, veiculo_id, current_user.empresa_id)
            routes = connection.execute(
                """
                SELECT
                    dado.numero_rota,
                    MIN(dado.capturado_em) AS primeiro_ponto_em,
                    MAX(dado.capturado_em) AS ultimo_ponto_em,
                    COUNT(*) AS quantidade_pontos,
                    COALESCE(
                        BOOL_OR(
                            hardware.data_rota_atual = dado.data_rota
                            AND hardware.numero_rota_atual = dado.numero_rota
                        ),
                        FALSE
                    ) AS em_andamento
                FROM dados_crus AS dado
                INNER JOIN hardware
                    ON hardware.hardware_id = dado.hardware_id
                WHERE dado.veiculo_id = %(veiculo_id)s
                  AND dado.data_rota = %(data)s
                  AND dado.numero_rota IS NOT NULL
                GROUP BY dado.data_rota, dado.numero_rota
                ORDER BY dado.numero_rota
                """,
                {"veiculo_id": veiculo_id, "data": data},
            ).fetchall()
    except HTTPException:
        raise
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel consultar as rotas",
        ) from error

    return {
        "veiculo_id": veiculo_id,
        "data": data,
        "total_rotas": len(routes),
        "rotas": routes,
    }


@router.get("/{numero_rota}", response_model=RouteDetailResponse)
def get_vehicle_route(
    veiculo_id: int = Path(gt=0),
    numero_rota: int = Path(gt=0),
    data: date = Query(),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            require_company_vehicle(connection, veiculo_id, current_user.empresa_id)
            points = connection.execute(
                """
                SELECT
                    status_id, latitude, longitude,
                    velocidade, capturado_em
                FROM dados_crus
                WHERE veiculo_id = %(veiculo_id)s
                  AND data_rota = %(data)s
                  AND numero_rota = %(numero_rota)s
                ORDER BY capturado_em, status_id
                """,
                {
                    "veiculo_id": veiculo_id,
                    "data": data,
                    "numero_rota": numero_rota,
                },
            ).fetchall()
            if not points:
                raise HTTPException(status_code=404, detail="Rota nao encontrada")

            current_route = connection.execute(
                """
                SELECT 1
                FROM hardware
                INNER JOIN veiculos
                    ON veiculos.hardware_id = hardware.hardware_id
                   AND veiculos.empresa_id = hardware.empresa_id
                WHERE veiculos.veiculo_id = %(veiculo_id)s
                  AND hardware.data_rota_atual = %(data)s
                  AND hardware.numero_rota_atual = %(numero_rota)s
                """,
                {
                    "veiculo_id": veiculo_id,
                    "data": data,
                    "numero_rota": numero_rota,
                },
            ).fetchone()
    except HTTPException:
        raise
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel consultar a rota",
        ) from error

    return {
        "veiculo_id": veiculo_id,
        "data": data,
        "numero_rota": numero_rota,
        "em_andamento": current_route is not None,
        "pontos": points,
    }
