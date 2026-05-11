"""Настройки приложения из окружения (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Загрузка `.env` при локальном запуске; в Docker переменные приходят из Compose."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    app_name: str = "VPh04 API"
    api_v1_prefix: str = "/api/v1"

    # Подпись cookie-сессии (Starlette SessionMiddleware). Минимум 32 байта в UTF-8.
    secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 14

    docs_enabled: bool = False

    @property
    def database_url_sync(self) -> str:
        """URL для Alembic и синхронных утилит: asyncpg → psycopg v3."""
        url = self.database_url
        if "+asyncpg" in url:
            return url.replace("+asyncpg", "+psycopg", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
