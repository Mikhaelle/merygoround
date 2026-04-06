"""SQLAlchemy implementation of the SpinSessionRepository."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from merygoround.domain.wheel.entities import SpinSession, SpinStatus
from merygoround.domain.wheel.repository import SpinSessionRepository
from merygoround.infrastructure.database.models.wheel import SpinSessionModel


class SqlAlchemySpinSessionRepository(SpinSessionRepository):
    """Concrete SpinSessionRepository backed by SQLAlchemy and PostgreSQL.

    Args:
        session: The async database session.
    """

    def __init__(self, session: AsyncSession, tz_name: str = "UTC") -> None:
        self._session = session
        self._tz_name = tz_name

    async def get_by_id(self, session_id: uuid.UUID) -> SpinSession | None:
        """Retrieve a spin session by its unique identifier.

        Args:
            session_id: The UUID of the spin session.

        Returns:
            The SpinSession domain entity if found, otherwise None.
        """
        model = await self._session.get(SpinSessionModel, session_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def get_by_user_id(
        self, user_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[SpinSession], int]:
        """Retrieve paginated spin sessions for a user.

        Args:
            user_id: The UUID of the user.
            page: Page number (1-indexed).
            per_page: Number of items per page.

        Returns:
            Tuple of (list of SpinSession entities, total count).
        """
        count_stmt = (
            select(func.count())
            .select_from(SpinSessionModel)
            .where(SpinSessionModel.user_id == user_id)
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        offset = (page - 1) * per_page
        stmt = (
            select(SpinSessionModel)
            .where(SpinSessionModel.user_id == user_id)
            .order_by(SpinSessionModel.spun_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self._session.execute(stmt)
        sessions = [self._to_domain(m) for m in result.scalars().all()]

        return sessions, total

    async def get_completed_counts_for_date(
        self, user_id: uuid.UUID, target_date: date
    ) -> dict[uuid.UUID, int]:
        """Return done counts (completed + skipped) per chore for the given date.

        Args:
            user_id: The UUID of the user.
            target_date: The date to check.

        Returns:
            Dict mapping chore UUID to number of done sessions on that date.
        """
        tz = ZoneInfo(self._tz_name)
        day_start = datetime.combine(target_date, time.min, tzinfo=tz).astimezone(timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=tz).astimezone(timezone.utc)

        stmt = (
            select(
                SpinSessionModel.selected_chore_id,
                func.count().label("cnt"),
            )
            .where(
                and_(
                    SpinSessionModel.user_id == user_id,
                    SpinSessionModel.status.in_(["COMPLETED", "DEACTIVATED"]),
                    SpinSessionModel.spun_at >= day_start,
                    SpinSessionModel.spun_at <= day_end,
                )
            )
            .group_by(SpinSessionModel.selected_chore_id)
        )
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def get_status_counts_for_date(
        self, user_id: uuid.UUID, target_date: date
    ) -> dict[uuid.UUID, dict[str, int]]:
        """Return per-status counts per chore for the given date.

        Args:
            user_id: The UUID of the user.
            target_date: The date to check.

        Returns:
            Dict mapping chore UUID to dict of status -> count.
        """
        tz = ZoneInfo(self._tz_name)
        day_start = datetime.combine(target_date, time.min, tzinfo=tz).astimezone(timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=tz).astimezone(timezone.utc)

        stmt = (
            select(
                SpinSessionModel.selected_chore_id,
                SpinSessionModel.status,
                func.count().label("cnt"),
            )
            .where(
                and_(
                    SpinSessionModel.user_id == user_id,
                    SpinSessionModel.spun_at >= day_start,
                    SpinSessionModel.spun_at <= day_end,
                )
            )
            .group_by(SpinSessionModel.selected_chore_id, SpinSessionModel.status)
        )
        result = await self._session.execute(stmt)
        counts: dict[uuid.UUID, dict[str, int]] = {}
        for chore_id, status, cnt in result.all():
            if chore_id not in counts:
                counts[chore_id] = {}
            counts[chore_id][status] = cnt
        return counts

    async def delete_for_chore_on_date(
        self, user_id: uuid.UUID, chore_id: uuid.UUID, target_date: date
    ) -> int:
        """Delete all spin sessions for a specific chore on the given date.

        Args:
            user_id: The UUID of the user.
            chore_id: The UUID of the chore.
            target_date: The date whose sessions should be removed.

        Returns:
            The number of deleted sessions.
        """
        tz = ZoneInfo(self._tz_name)
        day_start = datetime.combine(target_date, time.min, tzinfo=tz).astimezone(timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=tz).astimezone(timezone.utc)

        stmt = (
            delete(SpinSessionModel)
            .where(
                and_(
                    SpinSessionModel.user_id == user_id,
                    SpinSessionModel.selected_chore_id == chore_id,
                    SpinSessionModel.spun_at >= day_start,
                    SpinSessionModel.spun_at <= day_end,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def delete_for_date(
        self, user_id: uuid.UUID, target_date: date
    ) -> int:
        """Delete all spin sessions for a user on the given date.

        Args:
            user_id: The UUID of the user.
            target_date: The date whose sessions should be removed.

        Returns:
            The number of deleted sessions.
        """
        tz = ZoneInfo(self._tz_name)
        day_start = datetime.combine(target_date, time.min, tzinfo=tz).astimezone(timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=tz).astimezone(timezone.utc)

        stmt = (
            delete(SpinSessionModel)
            .where(
                and_(
                    SpinSessionModel.user_id == user_id,
                    SpinSessionModel.spun_at >= day_start,
                    SpinSessionModel.spun_at <= day_end,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def add(self, session: SpinSession) -> SpinSession:
        """Persist a new spin session.

        Args:
            session: The SpinSession domain entity to persist.

        Returns:
            The persisted SpinSession domain entity.
        """
        model = SpinSessionModel(
            id=session.id,
            user_id=session.user_id,
            selected_chore_id=session.selected_chore_id,
            chore_name=session.chore_name,
            spun_at=session.spun_at,
            completed_at=session.completed_at,
            status=session.status.value,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def update(self, session: SpinSession) -> SpinSession:
        """Update an existing spin session.

        Args:
            session: The SpinSession domain entity with updated state.

        Returns:
            The updated SpinSession domain entity.
        """
        model = await self._session.get(SpinSessionModel, session.id)
        if model is not None:
            model.status = session.status.value
            model.completed_at = session.completed_at
            await self._session.flush()
        return session

    def _to_domain(self, model: SpinSessionModel) -> SpinSession:
        """Map a SpinSessionModel ORM instance to a SpinSession domain entity."""
        return SpinSession(
            id=model.id,
            user_id=model.user_id,
            selected_chore_id=model.selected_chore_id,
            chore_name=model.chore_name,
            spun_at=model.spun_at,
            completed_at=model.completed_at,
            status=SpinStatus(model.status),
        )
