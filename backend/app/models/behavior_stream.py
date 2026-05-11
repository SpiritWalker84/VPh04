"""Анонимные снимки метрик с лендинга (постоянно дописываются, без связи с заявками)."""

from __future__ import annotations

from sqlalchemy import BigInteger, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class BehaviorStreamEntry(Base, TimestampMixin):
    __tablename__ = "behavior_stream"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    time_on_page_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    buttons_clicked: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cursor_positions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    return_frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
