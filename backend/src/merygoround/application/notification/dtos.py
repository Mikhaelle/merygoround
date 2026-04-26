"""Data transfer objects for the Notification application layer."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SubscribePushRequest(BaseModel):
    """Request DTO for creating or refreshing a push subscription.

    Attributes:
        endpoint: The push service endpoint URL.
        p256dh_key: The client public key for encryption.
        auth_key: The authentication secret.
        device_label: Optional friendly label for the device.
    """

    endpoint: str = Field(min_length=1)
    p256dh_key: str = Field(min_length=1)
    auth_key: str = Field(min_length=1)
    device_label: str | None = Field(default=None, max_length=100)


class DeviceResponse(BaseModel):
    """Response DTO representing a single device subscription with its prefs."""

    id: uuid.UUID
    endpoint: str
    enabled: bool
    interval_minutes: int
    quiet_hours_start: int | None
    quiet_hours_end: int | None
    last_notified_at: datetime | None
    device_label: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateDevicePreferencesRequest(BaseModel):
    """Request DTO for updating one device's notification preferences."""

    enabled: bool | None = None
    interval_minutes: int | None = Field(default=None, ge=1, le=1440)
    quiet_hours_start: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=None, ge=0, le=23)
    device_label: str | None = Field(default=None, max_length=100)
