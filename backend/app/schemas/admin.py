"""Схемы админ-каталога (услуги и диапазоны бюджета)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AdminSettingCreate(BaseModel):
    service_title: str = Field(..., max_length=500)
    budget_range: str = Field(..., max_length=255)
    is_active: bool = True
    sort_order: int = 0


class AdminSettingUpdate(BaseModel):
    service_title: str | None = Field(None, max_length=500)
    budget_range: str | None = Field(None, max_length=255)
    is_active: bool | None = None
    sort_order: int | None = None


class AdminSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_title: str
    budget_range: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
