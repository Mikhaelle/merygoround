"""kanban bucket: status on bucket_items, drop bucket_draws, add bucket_settings

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-26 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply Kanban refactor.

    - Drop bucket_draws (active draws are abandoned per product decision).
    - Add status / started_at / completed_at to bucket_items, default 'to_do'.
    - Create bucket_settings (per-user max_in_progress, default 2).
    """
    op.drop_index("ix_bucket_draws_active_user", table_name="bucket_draws")
    op.drop_index(op.f("ix_bucket_draws_user_id"), table_name="bucket_draws")
    op.drop_table("bucket_draws")

    op.add_column(
        "bucket_items",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="to_do",
        ),
    )
    op.add_column(
        "bucket_items",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "bucket_items",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_bucket_items_status"), "bucket_items", ["status"], unique=False
    )

    op.create_table(
        "bucket_settings",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "max_in_progress",
            sa.Integer(),
            nullable=False,
            server_default="2",
        ),
        sa.Column("id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_bucket_settings_user_id"),
        "bucket_settings",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Revert Kanban refactor."""
    op.drop_index(op.f("ix_bucket_settings_user_id"), table_name="bucket_settings")
    op.drop_table("bucket_settings")

    op.drop_index(op.f("ix_bucket_items_status"), table_name="bucket_items")
    op.drop_column("bucket_items", "completed_at")
    op.drop_column("bucket_items", "started_at")
    op.drop_column("bucket_items", "status")

    op.create_table(
        "bucket_draws",
        sa.Column("bucket_item_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("drawn_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_justification", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["bucket_item_id"], ["bucket_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bucket_draws_active_user",
        "bucket_draws",
        ["user_id"],
        unique=True,
        postgresql_where="status = 'active'",
    )
    op.create_index(
        op.f("ix_bucket_draws_user_id"), "bucket_draws", ["user_id"], unique=False
    )
