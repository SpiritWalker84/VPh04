"""Доступ к таблице behavior_stream."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior_stream import BehaviorStreamEntry


class BehaviorStreamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        time_on_page_seconds: int,
        buttons_clicked: str,
        cursor_positions: str,
        return_frequency: int,
    ) -> BehaviorStreamEntry:
        row = BehaviorStreamEntry(
            time_on_page_seconds=time_on_page_seconds,
            buttons_clicked=buttons_clicked,
            cursor_positions=cursor_positions,
            return_frequency=return_frequency,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def list_recent(self, skip: int, limit: int) -> list[BehaviorStreamEntry]:
        stmt = (
            select(BehaviorStreamEntry)
            .order_by(desc(BehaviorStreamEntry.created_at))
            .offset(skip)
            .limit(min(limit, 500))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def avg_daily_max_seconds(self, since: datetime) -> float:
        """Среднее дневных максимумов time_on_page за окно (по календарным дням UTC)."""
        stmt = text(
            """
            SELECT COALESCE(AVG(daily_max), 0)::double precision
            FROM (
                SELECT MAX(time_on_page_seconds) AS daily_max
                FROM behavior_stream
                WHERE created_at >= :since
                GROUP BY (DATE(created_at AT TIME ZONE 'UTC'))
            ) AS day_max
            """
        )
        res = await self._session.execute(stmt, {"since": since.astimezone(UTC)})
        val = res.scalar_one()
        return float(val or 0)

    async def iter_cursor_rows_since(self, since: datetime) -> list[str]:
        stmt = select(BehaviorStreamEntry.cursor_positions).where(
            BehaviorStreamEntry.created_at >= since.astimezone(UTC),
            BehaviorStreamEntry.cursor_positions != "",
        )
        result = await self._session.execute(stmt)
        return [r[0] for r in result.all()]

    async def count_since(self, since: datetime) -> int:
        stmt = select(func.count()).select_from(BehaviorStreamEntry).where(
            BehaviorStreamEntry.created_at >= since.astimezone(UTC),
        )
        res = await self._session.execute(stmt)
        return int(res.scalar_one() or 0)
