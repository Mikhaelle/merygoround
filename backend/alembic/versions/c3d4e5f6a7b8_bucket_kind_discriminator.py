"""bucket kind discriminator (adult / happy)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-26 22:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ``kind`` discriminator to bucket_items and bucket_settings.

    Existing rows default to 'adult'. The settings unique index is widened to
    ``(user_id, kind)`` so the same user can have one settings row per board.
    """
    op.add_column(
        "bucket_items",
        sa.Column(
            "kind",
            sa.String(length=20),
            nullable=False,
            server_default="adult",
        ),
    )
    op.create_index(
        op.f("ix_bucket_items_kind"), "bucket_items", ["kind"], unique=False
    )

    op.add_column(
        "bucket_settings",
        sa.Column(
            "kind",
            sa.String(length=20),
            nullable=False,
            server_default="adult",
        ),
    )

    op.drop_constraint("bucket_settings_user_id_key", "bucket_settings", type_="unique")
    op.drop_index("ix_bucket_settings_user_id", table_name="bucket_settings")
    op.create_index(
        op.f("ix_bucket_settings_user_id"),
        "bucket_settings",
        ["user_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_bucket_settings_user_kind",
        "bucket_settings",
        ["user_id", "kind"],
    )


def downgrade() -> None:
    """Revert the kind discriminator."""
    op.drop_constraint(
        "uq_bucket_settings_user_kind", "bucket_settings", type_="unique"
    )
    op.drop_index(op.f("ix_bucket_settings_user_id"), table_name="bucket_settings")
    op.create_index(
        "ix_bucket_settings_user_id", "bucket_settings", ["user_id"], unique=True
    )
    op.create_unique_constraint(
        "bucket_settings_user_id_key", "bucket_settings", ["user_id"]
    )
    op.drop_column("bucket_settings", "kind")

    op.drop_index(op.f("ix_bucket_items_kind"), table_name="bucket_items")
    op.drop_column("bucket_items", "kind")
