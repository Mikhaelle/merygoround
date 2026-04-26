"""SQLAlchemy ORM models for the Adult Bucket bounded context."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from merygoround.infrastructure.database.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class BucketItemModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """ORM model mapping to the 'bucket_items' table.

    Each row represents a card on a Kanban board. ``kind`` distinguishes between
    boards (e.g. 'adult' or 'happy') so the same table hosts every board.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the owning user.
        name: Display name.
        description: Detailed description.
        category: Optional category label.
        status: Kanban column ('to_do', 'in_progress', 'blocked', 'done').
        kind: Board this item belongs to ('adult', 'happy').
        started_at: First time the item entered IN_PROGRESS, if ever.
        completed_at: First time the item entered DONE, if ever.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "bucket_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="to_do", server_default="to_do", index=True
    )
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False, default="adult", server_default="adult", index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BucketSettingsModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """ORM model mapping to the 'bucket_settings' table.

    Stores per-user-and-kind Kanban configuration. ``(user_id, kind)`` is unique.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the owning user.
        kind: Board this settings row applies to.
        max_in_progress: Maximum number of items allowed in IN_PROGRESS.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "bucket_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "kind", name="uq_bucket_settings_user_kind"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False, default="adult", server_default="adult"
    )
    max_in_progress: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, server_default="2"
    )
