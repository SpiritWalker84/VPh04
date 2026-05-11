"""Схемы для регистрации / входа администраторов."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuthRegisterBody(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8, max_length=512)


class AuthLoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegistrationCheckResponse(BaseModel):
    """True, если в системе ещё нет администраторов (доступна первая регистрация)."""

    registration_open: bool


class AdminMeResponse(BaseModel):
    id: int
    username: str
