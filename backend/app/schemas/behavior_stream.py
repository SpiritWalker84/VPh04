"""Входящий поток метрик и агрегаты для админки."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BehaviorMetricsIngest(BaseModel):
    """Тело POST: application_id не сохраняется (анонимная аналитика)."""

    application_id: int = 0
    time_on_page: int = Field(0, ge=0)
    buttons_clicked: str = ""
    cursor_positions: str = ""
    return_frequency: int = Field(0, ge=0)


class BehaviorStreamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    time_on_page_seconds: int
    buttons_clicked: str
    cursor_positions: str
    return_frequency: int
    created_at: datetime
    updated_at: datetime


class HeatmapCell(BaseModel):
    x: int
    y: int
    count: int


class BehaviorStatsResponse(BaseModel):
    avg_daily_max_seconds_day: float
    avg_daily_max_seconds_week: float
    avg_daily_max_seconds_month: float
    stream_rows_last_30_days: int = Field(
        0,
        description="Число строк потока метрик за последние 30 суток (сырые POST раз в секунду).",
    )
    heatmap: list[HeatmapCell]
    heatmap_grid_px: int = 40
