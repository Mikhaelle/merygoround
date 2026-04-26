"""Repository interfaces for the Notification bounded context."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from merygoround.domain.notification.entities import PushSubscription


class PushSubscriptionRepository(ABC):
    """Abstract repository for PushSubscription persistence.

    Each push subscription represents a single device and now carries the
    notification preferences (enabled, interval, quiet hours) for that device.
    """

    @abstractmethod
    async def get_by_id(self, subscription_id: uuid.UUID) -> PushSubscription | None:
        """Retrieve a push subscription by its UUID."""

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> list[PushSubscription]:
        """Retrieve all push subscriptions for a user."""

    @abstractmethod
    async def get_enabled(self) -> list[PushSubscription]:
        """Retrieve every enabled push subscription across all users."""

    @abstractmethod
    async def get_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        """Retrieve a push subscription by its endpoint URL."""

    @abstractmethod
    async def add(self, subscription: PushSubscription) -> PushSubscription:
        """Persist a new push subscription."""

    @abstractmethod
    async def update(self, subscription: PushSubscription) -> PushSubscription:
        """Update a persisted push subscription."""

    @abstractmethod
    async def delete_by_id(self, subscription_id: uuid.UUID) -> None:
        """Remove a push subscription by its UUID."""

    @abstractmethod
    async def delete_by_endpoint(self, endpoint: str) -> None:
        """Remove a push subscription by its endpoint URL."""
