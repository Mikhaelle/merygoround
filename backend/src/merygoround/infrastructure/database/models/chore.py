"""SQLAlchemy ORM models for the Chores bounded context."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from merygoround.infrastructure.database.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class ChoreModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """ORM model mapping to the 'chores' table.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the owning user.
        name: Display name of the chore.
        estimated_duration_minutes: Duration in minutes (1-10).
        category: Optional category label.
        multiplicity: Number of wheel slots.
        time_weight_rules: JSON array of time-weight rule objects.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "chores"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    multiplicity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    time_weight_rules: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    reward_value: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("1.00"))
