"""Зависимости FastAPI: сессия БД, сервисы, доступ администратора."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_session
from app.core.passwords import verify_password
from app.services.admin import AdminSettingsService
from app.services.application import ApplicationService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_application_service(session: SessionDep) -> ApplicationService:
    return ApplicationService(session)


def get_admin_service(session: SessionDep) -> AdminSettingsService:
    return AdminSettingsService(session)


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
AdminServiceDep = Annotated[AdminSettingsService, Depends(get_admin_service)]

_SESSION_ADMIN_KEY = "admin"


def is_admin_session(request: Request) -> bool:
    return bool(request.session.get(_SESSION_ADMIN_KEY))


def require_admin(request: Request) -> None:
    """Доступ только после успешного POST /auth/login (cookie-сессия)."""
    if not request.session.get(_SESSION_ADMIN_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Требуется вход")


AdminSessionDep = Annotated[None, Depends(require_admin)]


def login_admin_session(request: Request) -> None:
    request.session[_SESSION_ADMIN_KEY] = True


def logout_admin_session(request: Request) -> None:
    request.session.pop(_SESSION_ADMIN_KEY, None)


def verify_admin_credentials(username: str, password: str) -> None:
    settings = get_settings()
    if username != settings.admin_username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Неверные учётные данные")
    if not verify_password(password, settings.admin_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Неверные учётные данные")
