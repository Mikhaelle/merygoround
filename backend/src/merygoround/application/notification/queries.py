"""Query use cases for the Notification bounded context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from merygoround.application.notification.dtos import DeviceResponse
from merygoround.application.shared.use_case import BaseQuery
from merygoround.domain.notification.exceptions import SubscriptionNotFoundError
from merygoround.domain.shared.exceptions import AuthorizationError

if TYPE_CHECKING:
    from merygoround.domain.notification.entities import PushSubscription
    from merygoround.domain.notification.repository import PushSubscriptionRepository


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
class GetDeviceInput:
    """Input for GetDeviceQuery."""

    user_id: uuid.UUID
    subscription_id: uuid.UUID


class ListDevicesQuery(BaseQuery[uuid.UUID, list[DeviceResponse]]):
    """Lists every device subscription that belongs to the user."""

    def __init__(self, push_repo: PushSubscriptionRepository) -> None:
        self._push_repo = push_repo

    async def execute(self, input_data: uuid.UUID) -> list[DeviceResponse]:
        subs = await self._push_repo.get_by_user_id(input_data)
        return [_to_response(s) for s in subs]


class GetDeviceQuery(BaseQuery[GetDeviceInput, DeviceResponse]):
    """Returns one device subscription, validating ownership."""

    def __init__(self, push_repo: PushSubscriptionRepository) -> None:
        self._push_repo = push_repo

    async def execute(self, input_data: GetDeviceInput) -> DeviceResponse:
        sub = await self._push_repo.get_by_id(input_data.subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError(str(input_data.subscription_id))
        if sub.user_id != input_data.user_id:
            raise AuthorizationError("You do not own this subscription")
        return _to_response(sub)
