"""Роутер: заявки."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import ApplicationServiceDep
from app.schemas.application import LeadApplicationCreate, LeadApplicationList, LeadApplicationRead

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=LeadApplicationRead, status_code=201)
async def create_application(
    payload: LeadApplicationCreate,
    service: ApplicationServiceDep,
) -> LeadApplicationRead:
    """Приём заявки; опционально — вложенный блок метрик поведения."""
    return await service.create(payload)


@router.get("", response_model=list[LeadApplicationList])
async def list_applications(
    service: ApplicationServiceDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[LeadApplicationList]:
    return await service.list_items(limit=limit, offset=offset)


@router.get("/{application_id}", response_model=LeadApplicationRead)
async def get_application(
    application_id: int,
    service: ApplicationServiceDep,
) -> LeadApplicationRead:
    return await service.get(application_id)
