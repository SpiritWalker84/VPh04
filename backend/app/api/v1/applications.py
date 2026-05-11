"""Роутер: заявки."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from app.api.deps import ApplicationServiceDep, CurrentAdminDep
from app.schemas.application import (
    ApplicationDashboardResponse,
    LeadApplicationAdminDetail,
    LeadApplicationAdminListItem,
    LeadApplicationCreate,
    LeadApplicationRead,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=LeadApplicationRead, status_code=201)
async def create_application(
    payload: LeadApplicationCreate,
    service: ApplicationServiceDep,
) -> LeadApplicationRead:
    """Приём заявки; опционально — вложенный блок метрик поведения."""
    return await service.create(payload)


@router.get("", response_model=list[LeadApplicationAdminListItem])
async def list_applications(
    _: CurrentAdminDep,
    service: ApplicationServiceDep,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    sort: Literal["priority", "recent"] = Query(
        "priority",
        description="priority — горячие выше; recent — только по дате создания",
    ),
) -> list[LeadApplicationAdminListItem]:
    """Список заявок для админки с оценкой приоритета."""
    return await service.list_admin(limit=limit, skip=skip, sort=sort)


@router.get("/dashboard", response_model=ApplicationDashboardResponse)
async def applications_dashboard(
    _: CurrentAdminDep,
    service: ApplicationServiceDep,
) -> ApplicationDashboardResponse:
    """Сводные метрики по заявкам (баллы и температуры — по последним N при большой базе)."""
    return await service.dashboard()


@router.get("/{application_id}", response_model=LeadApplicationAdminDetail)
async def get_application(
    application_id: int,
    _: CurrentAdminDep,
    service: ApplicationServiceDep,
) -> LeadApplicationAdminDetail:
    return await service.get_admin(application_id)
