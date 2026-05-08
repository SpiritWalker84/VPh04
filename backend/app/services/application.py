"""Сценарии использования заявок."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.application import ApplicationRepository
from app.schemas.application import LeadApplicationCreate, LeadApplicationRead, LeadApplicationList


class ApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ApplicationRepository(session)
        self._session = session

    async def create(self, data: LeadApplicationCreate) -> LeadApplicationRead:
        entity = await self._repo.create(data)
        await self._session.commit()
        loaded = await self._repo.get(entity.id)
        if loaded is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="create failed")
        return LeadApplicationRead.model_validate(loaded)

    async def get(self, application_id: int) -> LeadApplicationRead:
        entity = await self._repo.get(application_id)
        if entity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="application not found")
        return LeadApplicationRead.model_validate(entity)

    async def list_items(self, *, limit: int, offset: int) -> list[LeadApplicationList]:
        rows = await self._repo.list_page(limit=limit, offset=offset)
        return [LeadApplicationList.model_validate(r) for r in rows]
