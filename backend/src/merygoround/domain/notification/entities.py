"""Entities for the Notification bounded context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PushSubscription:
    """A Web Push subscription for a single device, with its own preferences.

    Settings are stored per device so a user can have, for example, the desktop
    notifying every hour while the phone notifies every 30 minutes (or is off).

    Args:
        id: Unique identifier (also used by the frontend to address the device).
        user_id: Owning user.
        endpoint: Push service endpoint URL.
        p256dh_key: Client public key for encryption.
        auth_key: Authentication secret.
        enabled: Whether this device is currently receiving notifications.
        interval_minutes: Minimum minutes between notifications on this device.
        quiet_hours_start: Start hour of quiet period (0-23), or None.
        quiet_hours_end: End hour of quiet period (0-23), or None.
        last_notified_at: Timestamp of the last successful push to this device.
        device_label: Optional friendly label (e.g. "iPhone").
        created_at: Subscription creation timestamp.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    endpoint: str = ""
    p256dh_key: str = ""
    auth_key: str = ""
    enabled: bool = True
    interval_minutes: int = 60
    quiet_hours_start: int | None = None
    quiet_hours_end: int | None = None
    last_notified_at: datetime | None = None
    device_label: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
