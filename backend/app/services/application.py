"""Сценарии использования заявок."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.application import ApplicationRepository
from app.schemas.application import (
    ApplicationDashboardResponse,
    LeadApplicationAdminDetail,
    LeadApplicationAdminListItem,
    LeadApplicationCreate,
    LeadApplicationRead,
    LeadScoringInsight,
)
from app.services.lead_scoring import score_lead


class ApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ApplicationRepository(session)
        self._session = session

    @staticmethod
    def _insight_for(entity: object) -> LeadScoringInsight:
        r = score_lead(
            budget_label=getattr(entity, "budget_label", None),
            company_size=getattr(entity, "company_size", None),
            role_type=getattr(entity, "role_type", None),
            business_niche=getattr(entity, "business_niche", None),
            task_category=getattr(entity, "task_category", None),
            product_interest=getattr(entity, "product_interest", None),
            result_deadline=getattr(entity, "result_deadline", None),
            comments=getattr(entity, "comments", None),
            need_scope=getattr(entity, "need_scope", None),
            business_info=getattr(entity, "business_info", None),
            task_scope=getattr(entity, "task_scope", None),
        )
        return LeadScoringInsight(
            priority_score=r.priority_score,
            temperature=r.temperature,
            temperature_label=r.temperature_label,
            summary=r.summary,
            recommended_department=r.recommended_department,
            personal_manager_recommended=r.personal_manager_recommended,
            worth_pursuing=r.worth_pursuing,
            reasons=r.reasons,
        )

    async def create(self, data: LeadApplicationCreate) -> LeadApplicationRead:
        entity = await self._repo.create(data)
        await self._session.commit()
        loaded = await self._repo.get(entity.id)
        if loaded is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="create failed")
        return LeadApplicationRead.model_validate(loaded)

    async def get_admin(self, application_id: int) -> LeadApplicationAdminDetail:
        entity = await self._repo.get(application_id)
        if entity is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="application not found")
        base = LeadApplicationRead.model_validate(entity).model_dump()
        base["scoring"] = self._insight_for(entity)
        return LeadApplicationAdminDetail.model_validate(base)

    async def list_admin(
        self,
        *,
        limit: int,
        skip: int,
        sort: Literal["priority", "recent"],
    ) -> list[LeadApplicationAdminListItem]:
        cap = min(500, max(limit + skip, limit + 50, 100))
        rows = await self._repo.list_page(limit=cap, offset=0)
        items: list[LeadApplicationAdminListItem] = []
        for e in rows:
            insight = self._insight_for(e)
            items.append(
                LeadApplicationAdminListItem(
                    id=e.id,
                    first_name=e.first_name,
                    last_name=e.last_name,
                    middle_name=e.middle_name,
                    budget_label=e.budget_label,
                    business_niche=e.business_niche,
                    company_size=e.company_size,
                    role_type=e.role_type,
                    result_deadline=e.result_deadline,
                    product_interest=e.product_interest,
                    preferred_contact_method=e.preferred_contact_method,
                    created_at=e.created_at,
                    scoring=insight,
                )
            )
        if sort == "priority":
            items.sort(
                key=lambda it: (-it.scoring.priority_score, -it.created_at.timestamp()),
            )
        else:
            items.sort(key=lambda it: -it.created_at.timestamp())
        return items[skip : skip + limit]

    async def dashboard(self) -> ApplicationDashboardResponse:
        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)
        new_last_7 = await self._repo.count_created_since(week_ago)
        total = await self._repo.count_all()
        cap = 3000
        take = min(total, cap)
        rows = await self._repo.list_recent_for_dashboard(take)
        hot = warm = cold = 0
        scores: list[int] = []
        pm = 0
        worth_n = 0
        for e in rows:
            ins = self._insight_for(e)
            scores.append(ins.priority_score)
            if ins.temperature == "hot":
                hot += 1
            elif ins.temperature == "warm":
                warm += 1
            else:
                cold += 1
            if ins.personal_manager_recommended:
                pm += 1
            if ins.worth_pursuing:
                worth_n += 1
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0
        return ApplicationDashboardResponse(
            applications_total=total,
            scored_for_breakdown=len(rows),
            scoring_capped=total > cap,
            hot_count=hot,
            warm_count=warm,
            cold_count=cold,
            avg_priority_score=avg,
            personal_manager_recommended_count=pm,
            worth_pursuing_count=worth_n,
            new_last_7_days=new_last_7,
        )
