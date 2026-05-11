"""JWT access tokens (HS256)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings


def create_access_token(*, subject: str, username: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta is not None else timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {"sub": subject, "username": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, object]:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
