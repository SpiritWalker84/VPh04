"""Метрики поведения на странице заявки; связь 1:1 с заявкой."""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BehaviorMetrics(Base, TimestampMixin):
    """
    Снимок событий с фронта (время, клики, курсор, сырый JSON).

    PK = FK на заявку (ровно одна строка на заявку).
    """

    __tablename__ = "behavior_metrics"

    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("applications.id", ondelete="CASCADE"),
        primary_key=True,
    )

    time_on_page_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    return_visits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    button_events: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    cursor_metrics: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    application: Mapped["LeadApplication"] = relationship(
        "LeadApplication",
        back_populates="behavior",
    )
