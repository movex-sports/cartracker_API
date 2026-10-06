"""Password hashing helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import bcrypt
import jwt

from app.config import get_settings


JWT_ALGORITHM = "HS256"
DUMMY_PASSWORD_HASH = bcrypt.hashpw(
    b"dummy-password-used-only-for-timing-protection",
    bcrypt.gensalt(),
)


def hash_password(password: str) -> str:
    """Return a bcrypt hash; the original password is never persisted."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    """Safely verify a password while reducing account-enumeration timing leaks."""
    candidate_hash = password_hash.encode("utf-8") if password_hash else DUMMY_PASSWORD_HASH
    try:
        valid = bcrypt.checkpw(password.encode("utf-8"), candidate_hash)
    except ValueError:
        valid = False
    return valid and password_hash is not None


def create_access_token(
    *,
    user_id: int,
    empresa_id: int,
    role: str,
) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    lifetime = timedelta(minutes=settings.access_token_minutes)
    expires_at = now + lifetime
    payload = {
        "sub": str(user_id),
        "empresa_id": empresa_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expires_at,
        "jti": str(uuid4()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Tipo de token invalido")
    return payload
