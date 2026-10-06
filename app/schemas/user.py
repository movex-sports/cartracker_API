"""User request and response contracts."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


ONLY_DIGITS = re.compile(r"\D")


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nome: str = Field(min_length=1, max_length=100)
    sobrenome: str = Field(min_length=1, max_length=150)
    cpf: str
    email: EmailStr
    rua: str = Field(min_length=1, max_length=150)
    numero: str = Field(min_length=1, max_length=20)
    cep: str
    bairro: str = Field(min_length=1, max_length=100)
    cidade: str = Field(min_length=1, max_length=100)
    estado: str
    contato: str = Field(min_length=1, max_length=20)
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    senha: str = Field(min_length=8, max_length=72)

    @field_validator("cpf")
    @classmethod
    def normalize_cpf(cls, value: str) -> str:
        normalized = ONLY_DIGITS.sub("", value)
        if len(normalized) != 11:
            raise ValueError("CPF deve conter 11 digitos")
        return normalized

    @field_validator("cep")
    @classmethod
    def normalize_cep(cls, value: str) -> str:
        normalized = ONLY_DIGITS.sub("", value)
        if len(normalized) != 8:
            raise ValueError("CEP deve conter 8 digitos")
        return normalized

    @field_validator("estado")
    @classmethod
    def normalize_estado(cls, value: str) -> str:
        normalized = value.upper()
        if not re.fullmatch(r"[A-Z]{2}", normalized):
            raise ValueError("Estado deve ser uma sigla com duas letras")
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.lower()

    @field_validator("senha")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Senha deve ocupar no maximo 72 bytes")
        return value


class UserResponse(BaseModel):
    user_id: int
    nome: str
    sobrenome: str
    cpf: str
    email: EmailStr
    rua: str
    numero: str
    cep: str
    bairro: str
    cidade: str
    estado: str
    contato: str
    username: str
    role: str
    is_owner: bool
    status: bool
