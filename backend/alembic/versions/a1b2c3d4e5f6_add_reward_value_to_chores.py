"""add reward_value to chores

Revision ID: a1b2c3d4e5f6
Revises: 9fb0502f52e5
Create Date: 2026-04-10 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "9fb0502f52e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chores",
        sa.Column(
            "reward_value",
            sa.Numeric(precision=6, scale=2),
            nullable=False,
            server_default="1.00",
        ),
    )


def downgrade() -> None:
    op.drop_column("chores", "reward_value")
