"""Reusable authentication dependencies for protected endpoints."""

from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_connection
from app.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    empresa_id: int
    role: str


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise unauthorized()

    try:
        claims = decode_access_token(credentials.credentials)
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise unauthorized() from error

    with get_connection() as connection:
        user = connection.execute(
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

    if not user:
        raise unauthorized()

    return AuthenticatedUser(
        user_id=user["user_id"],
        empresa_id=user["empresa_id"],
        role=user["role"],
    )


def require_company_owner(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> AuthenticatedUser:
    """Allow company-user management only to the role 1 account."""
    if current_user.role != "1":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o usuario principal pode gerenciar usuarios dependentes",
        )
    return current_user
