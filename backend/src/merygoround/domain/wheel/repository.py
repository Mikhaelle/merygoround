"""Repository interface for the Wheel bounded context."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from merygoround.domain.wheel.entities import SpinSession


class SpinSessionRepository(ABC):
    """Abstract repository for SpinSession persistence."""

    @abstractmethod
    async def get_by_id(self, session_id: uuid.UUID) -> SpinSession | None:
        """Retrieve a spin session by its unique identifier.

        Args:
            session_id: The UUID of the spin session.

        Returns:
            The SpinSession if found, otherwise None.
        """

    @abstractmethod
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

    @abstractmethod
    async def get_completed_counts_for_date(
        self, user_id: uuid.UUID, target_date: date
    ) -> dict[uuid.UUID, int]:
        """Return completion counts per chore for the given date.

        Args:
            user_id: The UUID of the user.
            target_date: The date to check.

        Returns:
            Dict mapping chore UUID to number of completions on that date.
        """

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    async def add(self, session: SpinSession) -> SpinSession:
        """Persist a new spin session.

        Args:
            session: The SpinSession entity to persist.

        Returns:
            The persisted SpinSession.
        """

    @abstractmethod
    async def update(self, session: SpinSession) -> SpinSession:
        """Update an existing spin session.

        Args:
            session: The SpinSession entity with updated state.

        Returns:
            The updated SpinSession.
        """

    @abstractmethod
    async def get_wallet_summary(
        self, user_id: uuid.UUID, today: date
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Return total completed earnings for today, this month, and this year.

        Args:
            user_id: The UUID of the user.
            today: The reference date (used for day/month/year filtering).

        Returns:
            Tuple of (today_total, month_total, year_total) in BRL.
        """
