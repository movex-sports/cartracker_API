"""User creation endpoint."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.database import get_connection
from app.schemas.user import UserCreate, UserResponse
from app.security import hash_password


router = APIRouter(prefix="/users", tags=["users"])


def duplicated_user_error(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="CPF, e-mail ou username ja cadastrado",
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> dict:
    password_hash = hash_password(payload.senha)

    try:
        with get_connection() as connection:
            empresa = connection.execute(
                """
                INSERT INTO empresas (nome, status, user_id)
                VALUES (NULL, TRUE, NULL)
                RETURNING empresa_id
                """
            ).fetchone()

            user = connection.execute(
                """
                INSERT INTO users (
                    nome, sobrenome, cpf, email, rua, numero, cep, bairro,
                    cidade, estado, contato, username, password_hash, role,
                    empresa_id, status
                )
                VALUES (
                    %(nome)s, %(sobrenome)s, %(cpf)s, %(email)s, %(rua)s,
                    %(numero)s, %(cep)s, %(bairro)s, %(cidade)s, %(estado)s,
                    %(contato)s, %(username)s, %(password_hash)s, '1',
                    %(empresa_id)s, TRUE
                )
                RETURNING user_id
                """,
                {
                    **payload.model_dump(exclude={"senha"}),
                    "password_hash": password_hash,
                    "empresa_id": empresa["empresa_id"],
                },
            ).fetchone()

            connection.execute(
                """
                UPDATE empresas
                SET user_id = %(user_id)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE empresa_id = %(empresa_id)s
                """,
                {
                    "user_id": user["user_id"],
                    "empresa_id": empresa["empresa_id"],
                },
            )

            user = connection.execute(
                """
                SELECT
                    user_id, nome, sobrenome, cpf, email, rua, numero, cep,
                    bairro, cidade, estado, contato, username, role,
                    empresa_id, status
                FROM users
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user["user_id"]},
            ).fetchone()
    except psycopg.errors.UniqueViolation as error:
        raise duplicated_user_error(error) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    return user


@router.post(
    "/dependentes",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dependent_user(
    payload: UserCreate,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    password_hash = hash_password(payload.senha)

    try:
        with get_connection() as connection:
            user = connection.execute(
                """
                INSERT INTO users (
                    nome, sobrenome, cpf, email, rua, numero, cep, bairro,
                    cidade, estado, contato, username, password_hash, role,
                    empresa_id, status
                )
                VALUES (
                    %(nome)s, %(sobrenome)s, %(cpf)s, %(email)s, %(rua)s,
                    %(numero)s, %(cep)s, %(bairro)s, %(cidade)s, %(estado)s,
                    %(contato)s, %(username)s, %(password_hash)s, '2',
                    %(empresa_id)s, TRUE
                )
                RETURNING
                    user_id, nome, sobrenome, cpf, email, rua, numero, cep,
                    bairro, cidade, estado, contato, username, role,
                    empresa_id, status
                """,
                {
                    **payload.model_dump(exclude={"senha"}),
                    "password_hash": password_hash,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
    except psycopg.errors.UniqueViolation as error:
        raise duplicated_user_error(error) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    return user
