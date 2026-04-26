"""SQLAlchemy implementation of the PushSubscriptionRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from merygoround.domain.notification.entities import PushSubscription
from merygoround.domain.notification.repository import PushSubscriptionRepository
from merygoround.infrastructure.database.models.notification import PushSubscriptionModel


class SqlAlchemyPushSubscriptionRepository(PushSubscriptionRepository):
    """Concrete PushSubscriptionRepository backed by SQLAlchemy and PostgreSQL.

    Args:
        session: The async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, subscription_id: uuid.UUID) -> PushSubscription | None:
        model = await self._session.get(PushSubscriptionModel, subscription_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[PushSubscription]:
        stmt = (
            select(PushSubscriptionModel)
            .where(PushSubscriptionModel.user_id == user_id)
            .order_by(PushSubscriptionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_enabled(self) -> list[PushSubscription]:
        stmt = select(PushSubscriptionModel).where(
            PushSubscriptionModel.enabled.is_(True)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        stmt = select(PushSubscriptionModel).where(
            PushSubscriptionModel.endpoint == endpoint
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def add(self, subscription: PushSubscription) -> PushSubscription:
        model = PushSubscriptionModel(
            id=subscription.id,
            user_id=subscription.user_id,
            endpoint=subscription.endpoint,
            p256dh_key=subscription.p256dh_key,
            auth_key=subscription.auth_key,
            enabled=subscription.enabled,
            interval_minutes=subscription.interval_minutes,
            quiet_hours_start=subscription.quiet_hours_start,
            quiet_hours_end=subscription.quiet_hours_end,
            last_notified_at=subscription.last_notified_at,
            device_label=subscription.device_label,
            created_at=subscription.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def update(self, subscription: PushSubscription) -> PushSubscription:
        model = await self._session.get(PushSubscriptionModel, subscription.id)
        if model is not None:
            model.endpoint = subscription.endpoint
            model.p256dh_key = subscription.p256dh_key
            model.auth_key = subscription.auth_key
            model.enabled = subscription.enabled
            model.interval_minutes = subscription.interval_minutes
            model.quiet_hours_start = subscription.quiet_hours_start
            model.quiet_hours_end = subscription.quiet_hours_end
            model.last_notified_at = subscription.last_notified_at
            model.device_label = subscription.device_label
            await self._session.flush()
        return subscription

    async def delete_by_id(self, subscription_id: uuid.UUID) -> None:
        stmt = delete(PushSubscriptionModel).where(
            PushSubscriptionModel.id == subscription_id
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def delete_by_endpoint(self, endpoint: str) -> None:
        stmt = delete(PushSubscriptionModel).where(
            PushSubscriptionModel.endpoint == endpoint
        )
        await self._session.execute(stmt)
        await self._session.flush()

    def _to_domain(self, model: PushSubscriptionModel) -> PushSubscription:
        return PushSubscription(
            id=model.id,
            user_id=model.user_id,
            endpoint=model.endpoint,
            p256dh_key=model.p256dh_key,
            auth_key=model.auth_key,
            enabled=model.enabled,
            interval_minutes=model.interval_minutes,
            quiet_hours_start=model.quiet_hours_start,
            quiet_hours_end=model.quiet_hours_end,
            last_notified_at=model.last_notified_at,
            device_label=model.device_label,
            created_at=model.created_at,
        )
