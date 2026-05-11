"""Роутер: справочник услуг (админ-данные)."""

from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import Response

from app.api.deps import AdminServiceDep, CurrentAdminDep
from app.schemas.admin import AdminSettingCreate, AdminSettingRead, AdminSettingUpdate

router = APIRouter(prefix="/admin/settings", tags=["admin-settings"])


@router.get("", response_model=list[AdminSettingRead])
async def list_active_settings(service: AdminServiceDep) -> list[AdminSettingRead]:
    """Только активные позиции — для публичной формы и выпадающих списков."""
    return await service.list_public()


@router.get("/all", response_model=list[AdminSettingRead])
async def list_all_settings(
    _: CurrentAdminDep,
    service: AdminServiceDep,
) -> list[AdminSettingRead]:
    """Полный список (включая неактивные) — только после входа в админку."""
    return await service.list_all()


@router.post("", response_model=AdminSettingRead, status_code=201)
async def create_setting(
    payload: AdminSettingCreate,
    _: CurrentAdminDep,
    service: AdminServiceDep,
) -> AdminSettingRead:
    return await service.create(payload)


@router.patch("/{setting_id}", response_model=AdminSettingRead)
async def update_setting(
    setting_id: int,
    payload: AdminSettingUpdate,
    _: CurrentAdminDep,
    service: AdminServiceDep,
) -> AdminSettingRead:
    return await service.update(setting_id, payload)


@router.delete("/{setting_id}", status_code=204)
async def delete_setting(
    setting_id: int,
    _: CurrentAdminDep,
    service: AdminServiceDep,
) -> Response:
    await service.delete(setting_id)
    return Response(status_code=204)
