"""Начальная схема: заявки, метрики поведения 1:1, админ-каталог."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260507_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("middle_name", sa.String(length=120), nullable=True),
        sa.Column("business_info", sa.Text(), nullable=True),
        sa.Column("budget_label", sa.String(length=255), nullable=True),
        sa.Column("preferred_contact_method", sa.String(length=120), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("business_niche", sa.String(length=255), nullable=True),
        sa.Column("company_size", sa.String(length=120), nullable=True),
        sa.Column("task_scope", sa.String(length=255), nullable=True),
        sa.Column("role_type", sa.String(length=64), nullable=True),
        sa.Column("business_scale", sa.String(length=120), nullable=True),
        sa.Column("need_scope", sa.String(length=255), nullable=True),
        sa.Column("result_deadline", sa.String(length=255), nullable=True),
        sa.Column("task_category", sa.String(length=255), nullable=True),
        sa.Column("product_interest", sa.String(length=255), nullable=True),
        sa.Column("convenient_contact_time", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "behavior_metrics",
        sa.Column("application_id", sa.BigInteger(), nullable=False),
        sa.Column("time_on_page_seconds", sa.Integer(), nullable=True),
        sa.Column("return_visits", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("button_events", postgresql.JSONB(), nullable=True),
        sa.Column("cursor_metrics", postgresql.JSONB(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("application_id"),
    )

    op.create_table(
        "admin_settings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("service_title", sa.String(length=500), nullable=False),
        sa.Column("budget_range", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_admin_settings_is_active_order", "admin_settings", ["is_active", "sort_order"])


def downgrade() -> None:
    op.drop_index("ix_admin_settings_is_active_order", table_name="admin_settings")
    op.drop_table("admin_settings")
    op.drop_table("behavior_metrics")
    op.drop_table("applications")
