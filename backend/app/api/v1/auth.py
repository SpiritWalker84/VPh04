"""JWT: проверка регистрации, первый админ, вход, /me, выход (на стороне клиента)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentAdminDep, SessionDep
from app.core.jwt_tokens import create_access_token
from app.core.passwords import hash_password, verify_password
from app.repositories.admin_account import AdminAccountRepository
from app.schemas.admin_account import (
    AdminMeResponse,
    AuthLoginBody,
    AuthRegisterBody,
    RegistrationCheckResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/check", response_model=RegistrationCheckResponse)
async def auth_check_public(session: SessionDep) -> RegistrationCheckResponse:
    """Публичный эндпоинт: можно ли зарегистрировать первого администратора."""
    repo = AdminAccountRepository(session)
    n = await repo.count_all()
    return RegistrationCheckResponse(registration_open=n == 0)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_first_admin(session: SessionDep, body: AuthRegisterBody) -> TokenResponse:
    repo = AdminAccountRepository(session)
    if await repo.count_all() > 0:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Регистрация закрыта")
    if await repo.get_by_username(body.username):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Логин занят")
    try:
        row = await repo.create(body.username.strip(), hash_password(body.password))
        await session.commit()
        await session.refresh(row)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Логин занят") from None

    token = create_access_token(subject=str(row.id), username=row.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(session: SessionDep, body: AuthLoginBody) -> TokenResponse:
    repo = AdminAccountRepository(session)
    row = await repo.get_by_username(body.username.strip())
    if row is None or not verify_password(body.password, row.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Неверные учётные данные")
    token = create_access_token(subject=str(row.id), username=row.username)
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout() -> dict[str, bool]:
    """JWT не хранится на сервере — клиент удаляет токен."""
    return {"ok": True}


@router.get("/me", response_model=AdminMeResponse)
async def me(admin: CurrentAdminDep) -> AdminMeResponse:
    return AdminMeResponse(id=admin.id, username=admin.username)
