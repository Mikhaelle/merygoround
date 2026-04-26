"""APScheduler-based notification scheduler (per-device)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from merygoround.infrastructure.database.repositories.push_subscription_repository import (
    SqlAlchemyPushSubscriptionRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from merygoround.domain.notification.entities import PushSubscription
    from merygoround.domain.notification.services import PushNotificationService

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """Scheduler that periodically sends per-device push notifications.

    Args:
        session_factory: Factory for creating async database sessions.
        push_service: Service for sending push notifications.
        tz_name: IANA timezone used to evaluate quiet hours per device.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        push_service: PushNotificationService,
        tz_name: str = "America/Sao_Paulo",
    ) -> None:
        self._session_factory = session_factory
        self._push_service = push_service
        self._tz = ZoneInfo(tz_name)
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        """Start the notification scheduler with a 60-second tick."""
        self._scheduler.add_job(
            self._check_and_send_notifications,
            "interval",
            seconds=60,
            id="notification_check",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("Notification scheduler started")

    def shutdown(self) -> None:
        """Shut down the notification scheduler gracefully."""
        self._scheduler.shutdown(wait=False)
        logger.info("Notification scheduler shut down")

    async def _check_and_send_notifications(self) -> None:
        """Iterate every enabled subscription and send when due."""
        async with self._session_factory() as session:
            try:
                repo = SqlAlchemyPushSubscriptionRepository(session)
                subs = await repo.get_enabled()
                now_utc = datetime.now(timezone.utc)

                for sub in subs:
                    if not self._should_notify(sub, now_utc):
                        continue
                    payload = {
                        "title": "MeryGoRound",
                        "body": "Hora de girar a roleta!",
                        "url": "/",
                    }
                    ok = await self._push_service.send(sub, payload)
                    if ok:
                        sub.last_notified_at = now_utc
                        await repo.update(sub)

                await session.commit()
            except Exception:
                logger.exception("Notification scheduler tick failed")
                await session.rollback()

    def _should_notify(self, sub: PushSubscription, now_utc: datetime) -> bool:
        """Decide whether to send a push to this device on this tick."""
        if sub.quiet_hours_start is not None and sub.quiet_hours_end is not None:
            local_hour = now_utc.astimezone(self._tz).hour
            start = sub.quiet_hours_start
            end = sub.quiet_hours_end
            if start <= end:
                if start <= local_hour < end:
                    return False
            elif local_hour >= start or local_hour < end:
                return False

        if sub.last_notified_at is None:
            return True

        elapsed = (now_utc - sub.last_notified_at).total_seconds() / 60
        return elapsed >= sub.interval_minutes
