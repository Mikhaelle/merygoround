"""Command use cases for the Notification bounded context."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from merygoround.application.notification.dtos import (
    DeviceResponse,
    SubscribePushRequest,
    UpdateDevicePreferencesRequest,
)
from merygoround.application.shared.use_case import BaseCommand
from merygoround.domain.notification.entities import PushSubscription
from merygoround.domain.notification.exceptions import SubscriptionNotFoundError
from merygoround.domain.shared.exceptions import AuthorizationError

if TYPE_CHECKING:
    from merygoround.domain.notification.repository import PushSubscriptionRepository
    from merygoround.domain.notification.services import PushNotificationService


def _to_response(sub: PushSubscription) -> DeviceResponse:
    """Convert a PushSubscription domain entity into a DeviceResponse DTO."""
    return DeviceResponse(
        id=sub.id,
        endpoint=sub.endpoint,
        enabled=sub.enabled,
        interval_minutes=sub.interval_minutes,
        quiet_hours_start=sub.quiet_hours_start,
        quiet_hours_end=sub.quiet_hours_end,
        last_notified_at=sub.last_notified_at,
        device_label=sub.device_label,
        created_at=sub.created_at,
    )


@dataclass
class SubscribePushInput:
    """Input for SubscribePushCommand."""

    user_id: uuid.UUID
    request: SubscribePushRequest


@dataclass
class UnsubscribeDeviceInput:
    """Input for UnsubscribeDeviceCommand."""

    user_id: uuid.UUID
    subscription_id: uuid.UUID


@dataclass
class UpdateDevicePreferencesInput:
    """Input for UpdateDevicePreferencesCommand."""

    user_id: uuid.UUID
    subscription_id: uuid.UUID
    request: UpdateDevicePreferencesRequest


@dataclass
class SendTestPushInput:
    """Input for SendTestPushCommand."""

    user_id: uuid.UUID
    subscription_id: uuid.UUID


class SubscribePushCommand(BaseCommand[SubscribePushInput, DeviceResponse]):
    """Registers (or refreshes) a push subscription for the current device.

    If the same endpoint already exists for this user we update its keys and
    keep the existing preferences. Cross-user endpoint reuse is denied.
    """

    def __init__(self, push_repo: PushSubscriptionRepository) -> None:
        self._push_repo = push_repo

    async def execute(self, input_data: SubscribePushInput) -> DeviceResponse:
        existing = await self._push_repo.get_by_endpoint(input_data.request.endpoint)
        if existing is not None and existing.user_id != input_data.user_id:
            raise AuthorizationError("Subscription endpoint belongs to another user")

        if existing is not None:
            existing.p256dh_key = input_data.request.p256dh_key
            existing.auth_key = input_data.request.auth_key
            if input_data.request.device_label is not None:
                existing.device_label = input_data.request.device_label
            existing.enabled = True
            existing.last_notified_at = datetime.now(UTC)
            existing = await self._push_repo.update(existing)
            return _to_response(existing)

        sub = PushSubscription(
            user_id=input_data.user_id,
            endpoint=input_data.request.endpoint,
            p256dh_key=input_data.request.p256dh_key,
            auth_key=input_data.request.auth_key,
            device_label=input_data.request.device_label,
            enabled=True,
            last_notified_at=datetime.now(UTC),
        )
        sub = await self._push_repo.add(sub)
        return _to_response(sub)


class UnsubscribeDeviceCommand(BaseCommand[UnsubscribeDeviceInput, None]):
    """Removes a single device's push subscription."""

    def __init__(self, push_repo: PushSubscriptionRepository) -> None:
        self._push_repo = push_repo

    async def execute(self, input_data: UnsubscribeDeviceInput) -> None:
        sub = await self._push_repo.get_by_id(input_data.subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError(str(input_data.subscription_id))
        if sub.user_id != input_data.user_id:
            raise AuthorizationError("You do not own this subscription")
        await self._push_repo.delete_by_id(input_data.subscription_id)


class UpdateDevicePreferencesCommand(
    BaseCommand[UpdateDevicePreferencesInput, DeviceResponse]
):
    """Updates the preferences of a single device."""

    def __init__(self, push_repo: PushSubscriptionRepository) -> None:
        self._push_repo = push_repo

    async def execute(
        self, input_data: UpdateDevicePreferencesInput
    ) -> DeviceResponse:
        sub = await self._push_repo.get_by_id(input_data.subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError(str(input_data.subscription_id))
        if sub.user_id != input_data.user_id:
            raise AuthorizationError("You do not own this subscription")

        req = input_data.request
        was_disabled = not sub.enabled
        if req.enabled is not None:
            sub.enabled = req.enabled
        if req.interval_minutes is not None:
            sub.interval_minutes = req.interval_minutes
        if req.quiet_hours_start is not None:
            sub.quiet_hours_start = req.quiet_hours_start
        if req.quiet_hours_end is not None:
            sub.quiet_hours_end = req.quiet_hours_end
        if req.device_label is not None:
            sub.device_label = req.device_label

        if was_disabled and sub.enabled:
            sub.last_notified_at = datetime.now(UTC)

        sub = await self._push_repo.update(sub)
        return _to_response(sub)


class SendTestPushCommand(BaseCommand[SendTestPushInput, None]):
    """Sends an immediate test notification to the given device."""

    def __init__(
        self,
        push_repo: PushSubscriptionRepository,
        push_service: PushNotificationService,
    ) -> None:
        self._push_repo = push_repo
        self._push_service = push_service

    async def execute(self, input_data: SendTestPushInput) -> None:
        sub = await self._push_repo.get_by_id(input_data.subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError(str(input_data.subscription_id))
        if sub.user_id != input_data.user_id:
            raise AuthorizationError("You do not own this subscription")

        payload = {
            "title": "MeryGoRound",
            "body": "Test notification - if you see this, push is working.",
            "url": "/",
        }
        ok = await self._push_service.send(sub, payload)
        if not ok:
            raise RuntimeError(f"Push send failed for subscription {sub.id}")
        # The actual JSON body is encoded inside the push service; we keep it
        # here only as a sanity assertion against a future signature change.
        assert json.dumps(payload)  # noqa: S101 - intentional invariant check
