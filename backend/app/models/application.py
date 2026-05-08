"""Заявка «тёплого» клиента."""

from __future__ import annotations

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class LeadApplication(Base, TimestampMixin):
    """
    Основная сущность заявки.

    Связанные таблицы создаются миграцией Alembic (`applications`).
    """

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    middle_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    business_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_contact_method: Mapped[str | None] = mapped_column(String(120), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    business_niche: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(120), nullable=True)
    task_scope: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    business_scale: Mapped[str | None] = mapped_column(String(120), nullable=True)
    need_scope: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_deadline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    task_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_interest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    convenient_contact_time: Mapped[str | None] = mapped_column(String(255), nullable=True)

    behavior: Mapped["BehaviorMetrics | None"] = relationship(
        "BehaviorMetrics",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
