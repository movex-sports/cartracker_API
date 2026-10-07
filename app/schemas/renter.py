"""Renter request and response contracts."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


ONLY_DIGITS = re.compile(r"\D")


class RenterCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    locatario_nome: str = Field(min_length=1, max_length=100)
    locatario_sobrenome: str = Field(min_length=1, max_length=150)
    locatario_cpf: str
    locatario_rua: str = Field(min_length=1, max_length=150)
    locatario_numero: str = Field(min_length=1, max_length=20)
    locatario_cep: str
    locatario_bairro: str = Field(min_length=1, max_length=100)
    locatario_cidade: str = Field(min_length=1, max_length=100)
    locatario_estado: str

    @field_validator("locatario_cpf")
    @classmethod
    def normalize_cpf(cls, value: str) -> str:
        normalized = ONLY_DIGITS.sub("", value)
        if len(normalized) != 11:
            raise ValueError("CPF deve conter 11 digitos")
        return normalized

    @field_validator("locatario_cep")
    @classmethod
    def normalize_cep(cls, value: str) -> str:
        normalized = ONLY_DIGITS.sub("", value)
        if len(normalized) != 8:
            raise ValueError("CEP deve conter 8 digitos")
        return normalized

    @field_validator("locatario_estado")
    @classmethod
    def normalize_estado(cls, value: str) -> str:
        normalized = value.upper()
        if not re.fullmatch(r"[A-Z]{2}", normalized):
            raise ValueError("Estado deve ser uma sigla com duas letras")
        return normalized


class RenterResponse(RenterCreate):
    locatario_id: int
    empresa_id: int
    veiculo_id: int
