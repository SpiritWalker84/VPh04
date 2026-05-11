"""Доступ к таблице заявок и метрик."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import LeadApplication
from app.models.behavior import BehaviorMetrics
from app.schemas.application import LeadApplicationCreate


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: LeadApplicationCreate) -> LeadApplication:
        entity = LeadApplication(
            first_name=data.first_name,
            last_name=data.last_name,
            middle_name=data.middle_name,
            business_info=data.business_info,
            budget_label=data.budget_label,
            preferred_contact_method=data.preferred_contact_method,
            comments=data.comments,
            business_niche=data.business_niche,
            company_size=data.company_size,
            task_scope=data.task_scope,
            role_type=data.role_type,
            business_scale=data.business_scale,
            need_scope=data.need_scope,
            result_deadline=data.result_deadline,
            task_category=data.task_category,
            product_interest=data.product_interest,
            convenient_contact_time=data.convenient_contact_time,
        )
        if data.behavior:
            entity.behavior = BehaviorMetrics(
                time_on_page_seconds=data.behavior.time_on_page_seconds,
                return_visits=data.behavior.return_visits,
                button_events=data.behavior.button_events,
                cursor_metrics=data.behavior.cursor_metrics,
                raw_payload=data.behavior.raw_payload,
            )
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity, attribute_names=["behavior"])
        return entity

    async def get(self, application_id: int) -> LeadApplication | None:
        stmt = (
            select(LeadApplication)
            .options(selectinload(LeadApplication.behavior))
            .where(LeadApplication.id == application_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_page(self, *, limit: int = 50, offset: int = 0) -> list[LeadApplication]:
        stmt = (
            select(LeadApplication)
            .order_by(desc(LeadApplication.created_at))
            .limit(min(limit, 500))
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(LeadApplication)
        res = await self._session.execute(stmt)
        return int(res.scalar_one() or 0)

    async def count_created_since(self, since: datetime) -> int:
        stmt = select(func.count()).select_from(LeadApplication).where(LeadApplication.created_at >= since)
        res = await self._session.execute(stmt)
        return int(res.scalar_one() or 0)

    async def list_recent_for_dashboard(self, limit: int) -> list[LeadApplication]:
        if limit <= 0:
            return []
        stmt = (
            select(LeadApplication)
            .order_by(desc(LeadApplication.created_at))
            .limit(min(limit, 5000))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
