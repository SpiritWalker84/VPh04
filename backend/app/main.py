"""Точка входа ASGI: FastAPI + OpenAPI за префиксом `/api` для Nginx."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_v1_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Резерв под прогрев пула; сейчас пул создаётся лениво при первом запросе."""
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    kwargs: dict = {
        "title": settings.app_name,
        "lifespan": lifespan,
    }
    if settings.docs_enabled:
        kwargs["docs_url"] = "/api/docs"
        kwargs["redoc_url"] = "/api/redoc"
        kwargs["openapi_url"] = "/api/openapi.json"
    else:
        kwargs["docs_url"] = None
        kwargs["redoc_url"] = None
        kwargs["openapi_url"] = None

    application = FastAPI(**kwargs)
    # Cookie-сессия для /admin: без HTTPS ставим https_only=False (см. README).
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="vph04_admin",
        max_age=14 * 24 * 60 * 60,
        same_site="lax",
        https_only=False,
    )
    application.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
