"""Зависимости FastAPI: сессия БД, сервисы, JWT и текущий администратор."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_tokens import decode_access_token
from app.core.database import get_session
from app.models.admin_account import AdminAccount
from app.repositories.admin_account import AdminAccountRepository
from app.services.admin import AdminSettingsService
from app.services.application import ApplicationService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_http_bearer = HTTPBearer(auto_error=False)


def get_application_service(session: SessionDep) -> ApplicationService:
    return ApplicationService(session)


def get_admin_service(session: SessionDep) -> AdminSettingsService:
    return AdminSettingsService(session)


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
AdminServiceDep = Annotated[AdminSettingsService, Depends(get_admin_service)]


async def get_current_admin(
    session: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
) -> AdminAccount:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Требуется токен")
    token = creds.credentials
    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен") from None

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")
    try:
        admin_id = int(str(sub))
    except (TypeError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен") from None

    repo = AdminAccountRepository(session)
    admin = await repo.get_by_id(admin_id)
    if admin is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return admin


CurrentAdminDep = Annotated[AdminAccount, Depends(get_current_admin)]
