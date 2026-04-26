"""Per-device notification API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from merygoround.api.config import Settings
from merygoround.api.dependencies import get_current_user, get_session, get_settings
from merygoround.application.notification.commands import (
    SendTestPushCommand,
    SendTestPushInput,
    SubscribePushCommand,
    SubscribePushInput,
    UnsubscribeDeviceCommand,
    UnsubscribeDeviceInput,
    UpdateDevicePreferencesCommand,
    UpdateDevicePreferencesInput,
)
from merygoround.application.notification.dtos import (
    DeviceResponse,
    SubscribePushRequest,
    UpdateDevicePreferencesRequest,
)
from merygoround.application.notification.queries import (
    GetDeviceInput,
    GetDeviceQuery,
    ListDevicesQuery,
)
from merygoround.infrastructure.database.repositories.push_subscription_repository import (
    SqlAlchemyPushSubscriptionRepository,
)
from merygoround.infrastructure.push.web_push_service import PyWebPushNotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _push_service(settings: Settings) -> PyWebPushNotificationService:
    """Build the push service from current settings."""
    return PyWebPushNotificationService(
        vapid_private_key=settings.VAPID_PRIVATE_KEY,
        vapid_claims={"sub": settings.VAPID_CLAIMS_EMAIL},
    )


@router.get("/devices", response_model=list[DeviceResponse])
async def list_devices(
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[DeviceResponse]:
    """List every device the user has subscribed for push notifications."""
    repo = SqlAlchemyPushSubscriptionRepository(session)
    return await ListDevicesQuery(repo).execute(user_id)


@router.post("/devices", response_model=DeviceResponse, status_code=201)
async def subscribe(
    body: SubscribePushRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DeviceResponse:
    """Register (or refresh) a push subscription for the current device."""
    repo = SqlAlchemyPushSubscriptionRepository(session)
    return await SubscribePushCommand(repo).execute(
        SubscribePushInput(user_id=user_id, request=body)
    )


@router.get("/devices/{subscription_id}", response_model=DeviceResponse)
async def get_device(
    subscription_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DeviceResponse:
    """Return one device subscription with its preferences."""
    repo = SqlAlchemyPushSubscriptionRepository(session)
    return await GetDeviceQuery(repo).execute(
        GetDeviceInput(user_id=user_id, subscription_id=subscription_id)
    )


@router.put("/devices/{subscription_id}", response_model=DeviceResponse)
async def update_device(
    subscription_id: uuid.UUID,
    body: UpdateDevicePreferencesRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DeviceResponse:
    """Update the preferences (enabled, interval, quiet hours) of one device."""
    repo = SqlAlchemyPushSubscriptionRepository(session)
    return await UpdateDevicePreferencesCommand(repo).execute(
        UpdateDevicePreferencesInput(
            user_id=user_id, subscription_id=subscription_id, request=body
        )
    )


@router.delete("/devices/{subscription_id}", status_code=204)
async def unsubscribe_device(
    subscription_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Remove the subscription of a single device."""
    repo = SqlAlchemyPushSubscriptionRepository(session)
    await UnsubscribeDeviceCommand(repo).execute(
        UnsubscribeDeviceInput(user_id=user_id, subscription_id=subscription_id)
    )


@router.post("/devices/{subscription_id}/test", status_code=204)
async def send_test_push(
    subscription_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Send an immediate test notification to the given device."""
    repo = SqlAlchemyPushSubscriptionRepository(session)
    push = _push_service(settings)
    await SendTestPushCommand(repo, push).execute(
        SendTestPushInput(user_id=user_id, subscription_id=subscription_id)
    )
