"""User creation endpoint."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, HTTPException, status

from app.database import get_connection
from app.schemas.user import UserCreate, UserResponse
from app.security import hash_password


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> dict:
    password_hash = hash_password(payload.senha)

    try:
        with get_connection() as connection:
            user = connection.execute(
                """
                INSERT INTO users (
                    nome, sobrenome, cpf, email, rua, numero, cep, bairro,
                    cidade, estado, contato, username, password_hash,
                    role, is_owner, status
                )
                VALUES (
                    %(nome)s, %(sobrenome)s, %(cpf)s, %(email)s, %(rua)s,
                    %(numero)s, %(cep)s, %(bairro)s, %(cidade)s, %(estado)s,
                    %(contato)s, %(username)s, %(password_hash)s,
                    '1', FALSE, TRUE
                )
                RETURNING
                    user_id, nome, sobrenome, cpf, email, rua, numero, cep,
                    bairro, cidade, estado, contato, username, role,
                    is_owner, status
                """,
                {
                    **payload.model_dump(exclude={"senha"}),
                    "password_hash": password_hash,
                },
            ).fetchone()
    except psycopg.errors.UniqueViolation as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF, e-mail ou username ja cadastrado",
        ) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel acessar o banco de dados",
        ) from error

    return user
