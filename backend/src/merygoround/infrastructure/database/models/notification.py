"""SQLAlchemy ORM models for the Notification bounded context."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from merygoround.infrastructure.database.models.base import Base, UUIDPrimaryKeyMixin


class PushSubscriptionModel(UUIDPrimaryKeyMixin, Base):
    """ORM model mapping to the 'push_subscriptions' table.

    A row represents a single device for a user, including its notification
    preferences (enabled flag, interval, quiet hours and last notified time).

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the subscribing user.
        endpoint: Push service endpoint URL (unique).
        p256dh_key: Client public key for encryption.
        auth_key: Authentication secret.
        enabled: Whether this device should receive scheduled notifications.
        interval_minutes: Minimum minutes between notifications on this device.
        quiet_hours_start: Start hour of quiet period (0-23) or null.
        quiet_hours_end: End hour of quiet period (0-23) or null.
        last_notified_at: Timestamp of the last successful notification.
        device_label: Optional friendly label for the device.
        created_at: Subscription creation timestamp.
    """

    __tablename__ = "push_subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh_key: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_key: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60, server_default="60"
    )
    quiet_hours_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quiet_hours_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    device_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
