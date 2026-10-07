"""User creation endpoint."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_dependencies import (
    AuthenticatedUser,
    require_authenticated_user,
    require_company_owner,
)
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
    current_user: AuthenticatedUser = Depends(require_company_owner),
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


@router.get("/me", response_model=UserResponse)
def get_authenticated_user(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    """Return the profile used to identify the authenticated user in the UI."""
    try:
        with get_connection() as connection:
            user = connection.execute(
                """
                SELECT
                    user_id, nome, sobrenome, cpf, email, rua, numero, cep,
                    bairro, cidade, estado, contato, username, role,
                    empresa_id, status
                FROM users
                WHERE user_id = %(user_id)s
                  AND empresa_id = %(empresa_id)s
                """,
                {
                    "user_id": current_user.user_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado",
        )

    return user


@router.get("/dependentes", response_model=list[UserResponse])
def list_dependent_users(
    current_user: AuthenticatedUser = Depends(require_company_owner),
) -> list[dict]:
    try:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    user_id, nome, sobrenome, cpf, email, rua, numero, cep,
                    bairro, cidade, estado, contato, username, role,
                    empresa_id, status
                FROM users
                WHERE empresa_id = %(empresa_id)s
                  AND role = '2'
                ORDER BY nome, sobrenome, user_id
                """,
                {"empresa_id": current_user.empresa_id},
            ).fetchall()
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error


@router.delete("/dependentes/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dependent_user(
    user_id: int,
    current_user: AuthenticatedUser = Depends(require_company_owner),
) -> None:
    try:
        with get_connection() as connection:
            deleted_user = connection.execute(
                """
                DELETE FROM users
                WHERE user_id = %(user_id)s
                  AND empresa_id = %(empresa_id)s
                  AND role = '2'
                RETURNING user_id
                """,
                {
                    "user_id": user_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not deleted_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario dependente nao encontrado",
                )
    except HTTPException:
        raise
    except psycopg.errors.ForeignKeyViolation as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuario possui registros vinculados e nao pode ser excluido",
        ) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error
