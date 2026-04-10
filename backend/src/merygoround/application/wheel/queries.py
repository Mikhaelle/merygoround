"""Query use cases for the Wheel bounded context."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from merygoround.application.shared.timezone import get_local_now
from merygoround.application.shared.use_case import BaseQuery
from merygoround.application.wheel.dtos import (
    DailyProgressItem,
    SpinHistoryItem,
    SpinHistoryResponse,
    WalletResponse,
    WheelSegmentResponse,
)

if TYPE_CHECKING:
    from merygoround.domain.chores.repository import ChoreRepository
    from merygoround.domain.wheel.repository import SpinSessionRepository
    from merygoround.domain.wheel.services import WheelSpinService


def _generate_color(name: str) -> str:
    """Generate a deterministic hex color from a string."""
    digest = hashlib.md5(name.encode()).hexdigest()  # noqa: S324
    return f"#{digest[:6]}"


class GetWheelSegmentsQuery(BaseQuery[uuid.UUID, list[WheelSegmentResponse]]):
    """Returns wheel segments with effective weights for the current hour.

    Excludes chores that were already completed or deactivated today.

    Args:
        chore_repo: Chore repository for loading user chores.
        spin_repo: Spin session repository for checking today's completions.
        spin_service: Domain service for weight calculation.
        tz_name: IANA timezone for date/hour calculations.
    """

    def __init__(
        self,
        chore_repo: ChoreRepository,
        spin_repo: SpinSessionRepository,
        spin_service: WheelSpinService,
        tz_name: str = "UTC",
    ) -> None:
        self._chore_repo = chore_repo
        self._spin_repo = spin_repo
        self._spin_service = spin_service
        self._tz_name = tz_name

    async def execute(self, input_data: uuid.UUID) -> list[WheelSegmentResponse]:
        """Build wheel segments for the user's chores.

        Args:
            input_data: The UUID of the authenticated user.

        Returns:
            List of WheelSegmentResponse DTOs excluding today's completed chores.
        """
        from merygoround.domain.chores.entities import Chore, WheelConfiguration
        from merygoround.domain.chores.value_objects import Multiplicity

        chores = await self._chore_repo.get_by_user_id(input_data)
        local_now = get_local_now(self._tz_name)

        completed_counts = await self._spin_repo.get_completed_counts_for_date(
            input_data, local_now.date()
        )

        segments: list[WheelSegmentResponse] = []
        for chore in chores:
            done = completed_counts.get(chore.id, 0)
            remaining = chore.wheel_config.multiplicity.value - done
            if remaining <= 0:
                continue

            adjusted = Chore(
                id=chore.id,
                user_id=chore.user_id,
                name=chore.name,
                estimated_duration=chore.estimated_duration,
                category=chore.category,
                wheel_config=WheelConfiguration(
                    multiplicity=Multiplicity(remaining),
                    time_weight_rules=chore.wheel_config.time_weight_rules,
                ),
                created_at=chore.created_at,
                updated_at=chore.updated_at,
            )
            effective_weight = self._spin_service.get_effective_weight(adjusted, local_now.hour)
            if effective_weight == 0:
                continue

            segments.append(
                WheelSegmentResponse(
                    chore_id=adjusted.id,
                    name=adjusted.name,
                    color=_generate_color(adjusted.name),
                    effective_weight=effective_weight,
                )
            )

        return segments


class GetDailyProgressQuery(BaseQuery[uuid.UUID, list[DailyProgressItem]]):
    """Returns daily completion/skip/deactivation progress per chore.

    Args:
        chore_repo: Chore repository for loading user chores.
        spin_repo: Spin session repository for checking today's counts.
        tz_name: IANA timezone for date calculations.
    """

    def __init__(
        self,
        chore_repo: ChoreRepository,
        spin_repo: SpinSessionRepository,
        tz_name: str = "UTC",
    ) -> None:
        self._chore_repo = chore_repo
        self._spin_repo = spin_repo
        self._tz_name = tz_name

    async def execute(self, input_data: uuid.UUID) -> list[DailyProgressItem]:
        """Build daily progress for all user chores.

        Args:
            input_data: The UUID of the authenticated user.

        Returns:
            List of DailyProgressItem DTOs.
        """
        chores = await self._chore_repo.get_by_user_id(input_data)
        local_now = get_local_now(self._tz_name)
        status_counts = await self._spin_repo.get_status_counts_for_date(
            input_data, local_now.date()
        )

        items: list[DailyProgressItem] = []
        for chore in chores:
            counts = status_counts.get(chore.id, {})
            items.append(
                DailyProgressItem(
                    chore_id=chore.id,
                    completed=counts.get("COMPLETED", 0),
                    skipped=counts.get("SKIPPED", 0),
                    deactivated=counts.get("DEACTIVATED", 0),
                    multiplicity=chore.wheel_config.multiplicity.value,
                )
            )
        return items


@dataclass
class GetSpinHistoryInput:
    """Input for GetSpinHistoryQuery.

    Attributes:
        user_id: The authenticated user.
        page: Page number.
        per_page: Items per page.
    """

    user_id: uuid.UUID
    page: int = 1
    per_page: int = 20


class GetSpinHistoryQuery(BaseQuery[GetSpinHistoryInput, SpinHistoryResponse]):
    """Retrieves paginated spin history for the authenticated user.

    Args:
        spin_repo: Spin session repository for lookup.
    """

    def __init__(self, spin_repo: SpinSessionRepository) -> None:
        self._spin_repo = spin_repo

    async def execute(self, input_data: GetSpinHistoryInput) -> SpinHistoryResponse:
        """Fetch paginated spin history.

        Args:
            input_data: Contains user ID and pagination parameters.

        Returns:
            SpinHistoryResponse with paginated spin sessions.
        """
        sessions, total = await self._spin_repo.get_by_user_id(
            input_data.user_id,
            page=input_data.page,
            per_page=input_data.per_page,
        )

        items = [
            SpinHistoryItem(
                id=s.id,
                chore_name=s.chore_name,
                spun_at=s.spun_at,
                completed_at=s.completed_at,
                status=s.status.value,
            )
            for s in sessions
        ]

        return SpinHistoryResponse(
            items=items,
            total=total,
            page=input_data.page,
            per_page=input_data.per_page,
        )


class GetWalletSummaryQuery(BaseQuery[uuid.UUID, WalletResponse]):
    """Returns the user's wallet earnings summary (today, month, year).

    Args:
        spin_repo: Spin session repository for earnings aggregation.
    """

    def __init__(self, spin_repo: SpinSessionRepository) -> None:
        self._spin_repo = spin_repo

    async def execute(self, input_data: uuid.UUID) -> WalletResponse:
        """Compute total BRL earnings for today, this month, and this year.

        Args:
            input_data: The UUID of the authenticated user.

        Returns:
            WalletResponse with the three period totals.
        """
        today = date.today()
        total_today, total_month, total_year = await self._spin_repo.get_wallet_summary(
            input_data, today
        )
        return WalletResponse(
            total_today=total_today,
            total_this_month=total_month,
            total_this_year=total_year,
        )
