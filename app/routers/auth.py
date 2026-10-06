"""Authentication endpoints."""

from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_connection
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token, decode_access_token, verify_password


router = APIRouter(prefix="/auth", tags=["authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


def find_active_user(login: str) -> dict | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                usuario.user_id,
                usuario.empresa_id,
                usuario.role,
                usuario.password_hash
            FROM users AS usuario
            INNER JOIN empresas AS empresa
                ON empresa.empresa_id = usuario.empresa_id
            WHERE (LOWER(usuario.username) = LOWER(%(login)s)
                OR LOWER(usuario.email) = LOWER(%(login)s))
              AND usuario.status = TRUE
              AND empresa.status = TRUE
            LIMIT 1
            """,
            {"login": login},
        ).fetchone()


def find_active_user_by_id(user_id: int) -> dict | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT usuario.user_id, usuario.empresa_id, usuario.role
            FROM users AS usuario
            INNER JOIN empresas AS empresa
                ON empresa.empresa_id = usuario.empresa_id
            WHERE usuario.user_id = %(user_id)s
              AND usuario.status = TRUE
              AND empresa.status = TRUE
            """,
            {"user_id": user_id},
        ).fetchone()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = find_active_user(payload.login)
    if not verify_password(payload.senha, user["password_hash"] if user else None):
        raise authentication_error()

    access_token, expires_in = create_access_token(
        user_id=user["user_id"],
        empresa_id=user["empresa_id"],
        role=user["role"],
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
    )


@router.post("/renew", response_model=TokenResponse)
def renew(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenResponse:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        claims = decode_access_token(credentials.credentials)
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise authentication_error() from error

    user = find_active_user_by_id(user_id)
    if not user:
        raise authentication_error()

    access_token, expires_in = create_access_token(
        user_id=user["user_id"],
        empresa_id=user["empresa_id"],
        role=user["role"],
    )
    return TokenResponse(access_token=access_token, expires_in=expires_in)
