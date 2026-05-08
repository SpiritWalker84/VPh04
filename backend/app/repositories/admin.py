"""CRUD по админ-настройкам."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminSetting
from app.schemas.admin import AdminSettingCreate, AdminSettingUpdate


class AdminSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: AdminSettingCreate) -> AdminSetting:
        row = AdminSetting(
            service_title=data.service_title,
            budget_range=data.budget_range,
            is_active=data.is_active,
            sort_order=data.sort_order,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get(self, setting_id: int) -> AdminSetting | None:
        result = await self._session.execute(select(AdminSetting).where(AdminSetting.id == setting_id))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[AdminSetting]:
        stmt = (
            select(AdminSetting)
            .where(AdminSetting.is_active.is_(True))
            .order_by(AdminSetting.sort_order, AdminSetting.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[AdminSetting]:
        stmt = select(AdminSetting).order_by(AdminSetting.sort_order, AdminSetting.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, row: AdminSetting, data: AdminSettingUpdate) -> AdminSetting:
        payload = data.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def delete(self, row: AdminSetting) -> None:
        await self._session.delete(row)
