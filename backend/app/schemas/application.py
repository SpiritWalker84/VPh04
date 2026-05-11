"""Схемы заявок и связанных метрик (вход/выход API)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BehaviorMetricsCreate(BaseModel):
    time_on_page_seconds: int | None = None
    return_visits: int = 0
    button_events: dict[str, Any] | list[Any] | None = None
    cursor_metrics: dict[str, Any] | list[Any] | None = None
    raw_payload: dict[str, Any] | None = None


class BehaviorMetricsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    time_on_page_seconds: int | None
    return_visits: int
    button_events: dict[str, Any] | list[Any] | None
    cursor_metrics: dict[str, Any] | list[Any] | None
    raw_payload: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class LeadApplicationCreate(BaseModel):
    first_name: str = Field(..., max_length=120)
    last_name: str = Field(..., max_length=120)
    middle_name: str | None = Field(None, max_length=120)

    business_info: str | None = None
    budget_label: str | None = Field(None, max_length=255)
    preferred_contact_method: str | None = Field(None, max_length=120)
    comments: str | None = None

    business_niche: str | None = Field(None, max_length=255)
    company_size: str | None = Field(None, max_length=120)
    task_scope: str | None = Field(None, max_length=255)
    role_type: str | None = Field(None, max_length=64)
    business_scale: str | None = Field(None, max_length=120)
    need_scope: str | None = Field(None, max_length=255)
    result_deadline: str | None = Field(None, max_length=255)
    task_category: str | None = Field(None, max_length=255)
    product_interest: str | None = Field(None, max_length=255)
    convenient_contact_time: str | None = Field(None, max_length=255)

    behavior: BehaviorMetricsCreate | None = None


class LeadApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    middle_name: str | None
    business_info: str | None
    budget_label: str | None
    preferred_contact_method: str | None
    comments: str | None
    business_niche: str | None
    company_size: str | None
    task_scope: str | None
    role_type: str | None
    business_scale: str | None
    need_scope: str | None
    result_deadline: str | None
    task_category: str | None
    product_interest: str | None
    convenient_contact_time: str | None
    created_at: datetime
    updated_at: datetime
    behavior: BehaviorMetricsRead | None = None


class LeadApplicationList(BaseModel):
    """Упрощённая выдача для списков (без вложенного behavior)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    created_at: datetime


class LeadScoringInsight(BaseModel):
    """Эвристическая оценка приоритета (для админки)."""

    priority_score: Annotated[int, Field(ge=0, le=100)]
    temperature: Literal["hot", "warm", "cold"]
    temperature_label: str
    summary: str
    recommended_department: str
    personal_manager_recommended: bool
    worth_pursuing: bool
    reasons: list[str] = Field(default_factory=list)


class LeadApplicationAdminListItem(BaseModel):
    """Строка списка заявок с приоритетом."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    middle_name: str | None
    budget_label: str | None
    business_niche: str | None
    company_size: str | None
    role_type: str | None
    result_deadline: str | None
    product_interest: str | None
    preferred_contact_method: str | None
    created_at: datetime
    scoring: LeadScoringInsight


class LeadApplicationAdminDetail(LeadApplicationRead):
    scoring: LeadScoringInsight


class ApplicationDashboardResponse(BaseModel):
    """Сводка по заявкам для дашборда админки."""

    applications_total: int
    scored_for_breakdown: int
    scoring_capped: bool
    hot_count: int
    warm_count: int
    cold_count: int
    avg_priority_score: float = Field(description="Средний балл приоритета по заявкам из разбивки")
    personal_manager_recommended_count: int
    worth_pursuing_count: int
    new_last_7_days: int = Field(description="Заявок за последние 7 суток (UTC)")
