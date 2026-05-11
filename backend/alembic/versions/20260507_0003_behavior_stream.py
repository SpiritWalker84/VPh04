"""Поток анонимных behavior-метрик (без FK на applications)."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260507_0003"
down_revision = "20260507_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "behavior_stream",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("time_on_page_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("buttons_clicked", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("cursor_positions", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("return_frequency", sa.Integer(), server_default=sa.text("0"), nullable=False),
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
    op.create_index("ix_behavior_stream_created_at", "behavior_stream", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_behavior_stream_created_at", table_name="behavior_stream")
    op.drop_table("behavior_stream")
