"""Бизнес-логика админ-каталога."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.admin import AdminSettingsRepository
from app.schemas.admin import AdminSettingCreate, AdminSettingRead, AdminSettingUpdate


class AdminSettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AdminSettingsRepository(session)
        self._session = session

    async def create(self, data: AdminSettingCreate) -> AdminSettingRead:
        row = await self._repo.create(data)
        await self._session.commit()
        await self._session.refresh(row)
        return AdminSettingRead.model_validate(row)

    async def list_public(self) -> list[AdminSettingRead]:
        rows = await self._repo.list_active()
        return [AdminSettingRead.model_validate(r) for r in rows]

    async def list_all(self) -> list[AdminSettingRead]:
        rows = await self._repo.list_all()
        return [AdminSettingRead.model_validate(r) for r in rows]

    async def update(self, setting_id: int, data: AdminSettingUpdate) -> AdminSettingRead:
        row = await self._repo.get(setting_id)
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="setting not found")
        await self._repo.update(row, data)
        await self._session.commit()
        await self._session.refresh(row)
        return AdminSettingRead.model_validate(row)

    async def delete(self, setting_id: int) -> None:
        row = await self._repo.get(setting_id)
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="setting not found")
        await self._repo.delete(row)
        await self._session.commit()
