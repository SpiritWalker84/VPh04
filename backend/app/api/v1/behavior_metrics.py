"""Анонимный поток метрик лендинга + выдача для админки."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query

from app.api.deps import CurrentAdminDep, SessionDep
from app.repositories.behavior_stream import BehaviorStreamRepository
from app.schemas.behavior_stream import BehaviorMetricsIngest, BehaviorStatsResponse, BehaviorStreamRead, HeatmapCell
from app.services.behavior_stats import build_heatmap

router = APIRouter(prefix="/behavior-metrics", tags=["behavior-metrics"])


@router.post("", status_code=201)
async def ingest_behavior(
    body: BehaviorMetricsIngest,
    session: SessionDep,
) -> dict[str, bool]:
    """Публичный приём: application_id из тела не сохраняется."""
    repo = BehaviorStreamRepository(session)
    await repo.create(
        time_on_page_seconds=body.time_on_page,
        buttons_clicked=body.buttons_clicked,
        cursor_positions=body.cursor_positions,
        return_frequency=body.return_frequency,
    )
    return {"ok": True}


@router.get("", response_model=list[BehaviorStreamRead])
async def list_behavior_samples(
    _: CurrentAdminDep,
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[BehaviorStreamRead]:
    repo = BehaviorStreamRepository(session)
    rows = await repo.list_recent(skip, limit)
    return [BehaviorStreamRead.model_validate(r) for r in rows]


@router.get("/stats", response_model=BehaviorStatsResponse)
async def behavior_stats(_: CurrentAdminDep, session: SessionDep) -> BehaviorStatsResponse:
    repo = BehaviorStreamRepository(session)
    now = datetime.now(UTC)
    day = await repo.avg_daily_max_seconds(now - timedelta(days=1))
    week = await repo.avg_daily_max_seconds(now - timedelta(days=7))
    month = await repo.avg_daily_max_seconds(now - timedelta(days=30))

    since_hm = now - timedelta(days=30)
    stream_rows = await repo.count_since(since_hm)
    cursor_payloads = await repo.iter_cursor_rows_since(since_hm)
    cells = build_heatmap(cursor_payloads, grid=40)

    return BehaviorStatsResponse(
        avg_daily_max_seconds_day=day,
        avg_daily_max_seconds_week=week,
        avg_daily_max_seconds_month=month,
        stream_rows_last_30_days=stream_rows,
        heatmap=[HeatmapCell.model_validate(c) for c in cells],
        heatmap_grid_px=40,
    )
