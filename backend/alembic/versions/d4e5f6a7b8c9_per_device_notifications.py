"""Per-device push notification settings

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-26 23:00:00.000000

Each row in push_subscriptions now carries its own preferences
(enabled, interval, quiet hours, last_notified_at, device_label).

Existing notification_preferences rows are migrated into every push_subscription
of the same user, then notification_preferences is dropped.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Move notification settings from notification_preferences to push_subscriptions."""
    op.add_column(
        "push_subscriptions",
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "push_subscriptions",
        sa.Column(
            "interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
    )
    op.add_column(
        "push_subscriptions",
        sa.Column("quiet_hours_start", sa.Integer(), nullable=True),
    )
    op.add_column(
        "push_subscriptions",
        sa.Column("quiet_hours_end", sa.Integer(), nullable=True),
    )
    op.add_column(
        "push_subscriptions",
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "push_subscriptions",
        sa.Column("device_label", sa.String(length=100), nullable=True),
    )

    op.execute(
        """
        UPDATE push_subscriptions ps
        SET enabled = np.enabled,
            interval_minutes = np.interval_minutes,
            quiet_hours_start = np.quiet_hours_start,
            quiet_hours_end = np.quiet_hours_end,
            last_notified_at = np.last_notified_at
        FROM notification_preferences np
        WHERE np.user_id = ps.user_id
        """
    )

    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")


def downgrade() -> None:
    """Recreate notification_preferences and remove per-device columns."""
    op.create_table(
        "notification_preferences",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("quiet_hours_start", sa.Integer(), nullable=True),
        sa.Column("quiet_hours_end", sa.Integer(), nullable=True),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
        unique=True,
    )

    op.drop_column("push_subscriptions", "device_label")
    op.drop_column("push_subscriptions", "last_notified_at")
    op.drop_column("push_subscriptions", "quiet_hours_end")
    op.drop_column("push_subscriptions", "quiet_hours_start")
    op.drop_column("push_subscriptions", "interval_minutes")
    op.drop_column("push_subscriptions", "enabled")
