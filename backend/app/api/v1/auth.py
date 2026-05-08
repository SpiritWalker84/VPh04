"""Вход / выход администратора (cookie-сессия, HTTP)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.api.deps import (
    is_admin_session,
    login_admin_session,
    logout_admin_session,
    verify_admin_credentials,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)


@router.post("/login")
async def login(request: Request, body: LoginBody) -> dict[str, bool]:
    verify_admin_credentials(body.username, body.password)
    login_admin_session(request)
    return {"ok": True}


@router.post("/logout")
async def logout(request: Request) -> dict[str, bool]:
    logout_admin_session(request)
    return {"ok": True}


@router.get("/me")
async def me(request: Request) -> dict[str, bool]:
    return {"authenticated": is_admin_session(request)}
