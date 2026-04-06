"""Tests for the Wheel bounded context query use cases."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from merygoround.application.wheel.queries import (
    GetDailyProgressQuery,
    GetSpinHistoryInput,
    GetSpinHistoryQuery,
    GetWheelSegmentsQuery,
)
from merygoround.domain.chores.entities import Chore, WheelConfiguration
from merygoround.domain.chores.value_objects import Duration, Multiplicity, TimeWeightRule
from merygoround.domain.wheel.entities import SpinSession, SpinStatus

from datetime import datetime, timezone


@pytest.fixture
def user_id() -> uuid.UUID:
    """Provide a fixed user UUID for tests."""
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def chore_repo() -> AsyncMock:
    """Provide a mock chore repository."""
    return AsyncMock()


@pytest.fixture
def spin_repo() -> AsyncMock:
    """Provide a mock spin session repository."""
    return AsyncMock()


@pytest.fixture
def spin_service() -> MagicMock:
    """Provide a mock wheel spin service."""
    service = MagicMock()
    service.get_effective_weight.return_value = 1.0
    return service


def _make_chore(user_id: uuid.UUID, name: str = "Test", multiplicity: int = 1) -> Chore:
    """Create a Chore entity for testing."""
    return Chore(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        estimated_duration=Duration(5),
        wheel_config=WheelConfiguration(
            multiplicity=Multiplicity(multiplicity),
            time_weight_rules=[],
        ),
    )


class TestGetWheelSegmentsQuery:
    """Test suite for GetWheelSegmentsQuery."""

    async def test_returns_all_chores_when_none_completed(
        self, user_id, chore_repo, spin_repo, spin_service
    ) -> None:
        """All chores appear as segments when nothing is completed today."""
        chores = [_make_chore(user_id, f"Chore {i}") for i in range(3)]
        chore_repo.get_by_user_id.return_value = chores
        spin_repo.get_completed_counts_for_date.return_value = {}

        query = GetWheelSegmentsQuery(chore_repo, spin_repo, spin_service, tz_name="UTC")
        segments = await query.execute(user_id)

        assert len(segments) == 3

    async def test_excludes_fully_completed_chores(
        self, user_id, chore_repo, spin_repo, spin_service
    ) -> None:
        """Chores at max multiplicity are excluded from segments."""
        c1 = _make_chore(user_id, "Done", multiplicity=1)
        c2 = _make_chore(user_id, "Available", multiplicity=1)
        chore_repo.get_by_user_id.return_value = [c1, c2]
        spin_repo.get_completed_counts_for_date.return_value = {c1.id: 1}

        query = GetWheelSegmentsQuery(chore_repo, spin_repo, spin_service, tz_name="UTC")
        segments = await query.execute(user_id)

        assert len(segments) == 1
        assert segments[0].name == "Available"

    async def test_adjusts_multiplicity_for_partial_completion(
        self, user_id, chore_repo, spin_repo, spin_service
    ) -> None:
        """Partially completed chores still appear with reduced multiplicity."""
        chore = _make_chore(user_id, "Partial", multiplicity=3)
        chore_repo.get_by_user_id.return_value = [chore]
        spin_repo.get_completed_counts_for_date.return_value = {chore.id: 1}

        query = GetWheelSegmentsQuery(chore_repo, spin_repo, spin_service, tz_name="UTC")
        segments = await query.execute(user_id)

        assert len(segments) == 1

    async def test_returns_empty_when_all_done(
        self, user_id, chore_repo, spin_repo, spin_service
    ) -> None:
        """Returns empty list when all chores are completed for the day."""
        chore = _make_chore(user_id, multiplicity=2)
        chore_repo.get_by_user_id.return_value = [chore]
        spin_repo.get_completed_counts_for_date.return_value = {chore.id: 2}

        query = GetWheelSegmentsQuery(chore_repo, spin_repo, spin_service, tz_name="UTC")
        segments = await query.execute(user_id)

        assert len(segments) == 0


class TestGetDailyProgressQuery:
    """Test suite for GetDailyProgressQuery."""

    async def test_returns_progress_for_all_chores(
        self, user_id, chore_repo, spin_repo
    ) -> None:
        """Returns progress items for every user chore."""
        chores = [_make_chore(user_id, f"Chore {i}", multiplicity=2) for i in range(3)]
        chore_repo.get_by_user_id.return_value = chores
        spin_repo.get_status_counts_for_date.return_value = {
            chores[0].id: {"COMPLETED": 1},
            chores[1].id: {"SKIPPED": 1},
        }

        query = GetDailyProgressQuery(chore_repo, spin_repo, tz_name="UTC")
        items = await query.execute(user_id)

        assert len(items) == 3
        progress_map = {str(item.chore_id): item for item in items}
        assert progress_map[str(chores[0].id)].completed == 1
        assert progress_map[str(chores[0].id)].skipped == 0
        assert progress_map[str(chores[1].id)].skipped == 1
        assert progress_map[str(chores[2].id)].completed == 0
        assert progress_map[str(chores[2].id)].skipped == 0

    async def test_returns_correct_multiplicity(
        self, user_id, chore_repo, spin_repo
    ) -> None:
        """Each progress item includes the chore's multiplicity."""
        chore = _make_chore(user_id, multiplicity=5)
        chore_repo.get_by_user_id.return_value = [chore]
        spin_repo.get_status_counts_for_date.return_value = {}

        query = GetDailyProgressQuery(chore_repo, spin_repo, tz_name="UTC")
        items = await query.execute(user_id)

        assert items[0].multiplicity == 5

    async def test_returns_empty_for_no_chores(
        self, user_id, chore_repo, spin_repo
    ) -> None:
        """Returns empty list when user has no chores."""
        chore_repo.get_by_user_id.return_value = []
        spin_repo.get_status_counts_for_date.return_value = {}

        query = GetDailyProgressQuery(chore_repo, spin_repo, tz_name="UTC")
        items = await query.execute(user_id)

        assert items == []

    async def test_includes_deactivated_count(
        self, user_id, chore_repo, spin_repo
    ) -> None:
        """Progress includes deactivated count when present."""
        chore = _make_chore(user_id, multiplicity=3)
        chore_repo.get_by_user_id.return_value = [chore]
        spin_repo.get_status_counts_for_date.return_value = {
            chore.id: {"COMPLETED": 1, "DEACTIVATED": 1},
        }

        query = GetDailyProgressQuery(chore_repo, spin_repo, tz_name="UTC")
        items = await query.execute(user_id)

        assert items[0].completed == 1
        assert items[0].deactivated == 1
        assert items[0].skipped == 0


class TestGetSpinHistoryQuery:
    """Test suite for GetSpinHistoryQuery."""

    async def test_returns_paginated_history(self, user_id, spin_repo) -> None:
        """Returns paginated spin history with correct metadata."""
        chore_id = uuid.uuid4()
        sessions = [
            SpinSession(
                user_id=user_id,
                selected_chore_id=chore_id,
                chore_name=f"Chore {i}",
                spun_at=datetime.now(timezone.utc),
                status=SpinStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]
        spin_repo.get_by_user_id.return_value = (sessions, 3)

        query = GetSpinHistoryQuery(spin_repo)
        result = await query.execute(
            GetSpinHistoryInput(user_id=user_id, page=1, per_page=10)
        )

        assert len(result.items) == 3
        assert result.total == 3
        assert result.page == 1
        assert result.items[0].status == "COMPLETED"

    async def test_returns_empty_history(self, user_id, spin_repo) -> None:
        """Returns empty items list when user has no spin history."""
        spin_repo.get_by_user_id.return_value = ([], 0)

        query = GetSpinHistoryQuery(spin_repo)
        result = await query.execute(
            GetSpinHistoryInput(user_id=user_id, page=1, per_page=10)
        )

        assert result.items == []
        assert result.total == 0
