"""Сводный роутер API v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin_settings, applications, auth

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router)
api_v1_router.include_router(applications.router)
api_v1_router.include_router(admin_settings.router)


@api_v1_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
