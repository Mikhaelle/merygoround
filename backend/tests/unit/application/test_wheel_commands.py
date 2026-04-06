"""Tests for the Wheel bounded context command use cases."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from merygoround.application.wheel.commands import (
    CompleteSpinInput,
    CompleteSpinSessionCommand,
    QuickCompleteChoreCommand,
    QuickCompleteChoreInput,
    QuickDeactivateChoreCommand,
    QuickDeactivateChoreInput,
    QuickSkipChoreCommand,
    QuickSkipChoreInput,
    ResetChoreCommand,
    ResetChoreInput,
    ResetDailyWheelCommand,
    ResetDailyWheelInput,
    SkipSpinInput,
    SkipSpinSessionCommand,
    SpinWheelCommand,
    SpinWheelInput,
)
from merygoround.domain.chores.entities import Chore, WheelConfiguration
from merygoround.domain.chores.value_objects import Duration, Multiplicity
from merygoround.domain.shared.exceptions import AuthorizationError, EntityNotFoundError, ValidationError
from merygoround.domain.wheel.entities import SpinSession, SpinStatus
from merygoround.domain.wheel.exceptions import NoChoresAvailableError


@pytest.fixture
def user_id() -> uuid.UUID:
    """Provide a fixed user UUID for tests."""
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def other_user_id() -> uuid.UUID:
    """Provide a different user UUID for ownership tests."""
    return uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


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
    return MagicMock()


def _make_chore(user_id: uuid.UUID, name: str = "Test Chore", multiplicity: int = 1) -> Chore:
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


def _make_session(
    user_id: uuid.UUID,
    chore_id: uuid.UUID,
    status: SpinStatus = SpinStatus.PENDING,
) -> SpinSession:
    """Create a SpinSession entity for testing."""
    return SpinSession(
        id=uuid.uuid4(),
        user_id=user_id,
        selected_chore_id=chore_id,
        chore_name="Test Chore",
        spun_at=datetime.now(timezone.utc),
        status=status,
    )


class TestSpinWheelCommand:
    """Test suite for SpinWheelCommand."""

    async def test_spin_creates_pending_session(
        self, user_id, chore_repo, spin_repo, spin_service
    ) -> None:
        """Spinning the wheel creates a PENDING spin session."""
        chore = _make_chore(user_id)
        chore_repo.get_by_user_id.return_value = [chore]
        spin_repo.get_completed_counts_for_date.return_value = {}
        spin_service.spin.return_value = chore
        spin_repo.add.side_effect = lambda s: s

        command = SpinWheelCommand(chore_repo, spin_repo, spin_service, tz_name="UTC")
        result = await command.execute(SpinWheelInput(user_id=user_id))

        assert result.status == "PENDING"
        spin_repo.add.assert_called_once()

    async def test_spin_excludes_completed_chores(
        self, user_id, chore_repo, spin_repo, spin_service
    ) -> None:
        """Chores that reached daily multiplicity are excluded from the spin."""
        chore = _make_chore(user_id, multiplicity=1)
        chore_repo.get_by_user_id.return_value = [chore]
        spin_repo.get_completed_counts_for_date.return_value = {chore.id: 1}

        spin_service.spin.side_effect = NoChoresAvailableError()

        command = SpinWheelCommand(chore_repo, spin_repo, spin_service, tz_name="UTC")
        with pytest.raises(NoChoresAvailableError):
            await command.execute(SpinWheelInput(user_id=user_id))

    async def test_spin_adjusts_remaining_multiplicity(
        self, user_id, chore_repo, spin_repo, spin_service
    ) -> None:
        """Partial completions reduce the remaining multiplicity passed to spin."""
        chore = _make_chore(user_id, multiplicity=3)
        chore_repo.get_by_user_id.return_value = [chore]
        spin_repo.get_completed_counts_for_date.return_value = {chore.id: 1}
        spin_repo.add.side_effect = lambda s: s

        captured_chores = []

        def capture_spin(chores, hour):
            captured_chores.extend(chores)
            return chores[0]

        spin_service.spin.side_effect = capture_spin

        command = SpinWheelCommand(chore_repo, spin_repo, spin_service, tz_name="UTC")
        await command.execute(SpinWheelInput(user_id=user_id))

        assert len(captured_chores) == 1
        assert captured_chores[0].wheel_config.multiplicity.value == 2


class TestCompleteSpinSessionCommand:
    """Test suite for CompleteSpinSessionCommand."""

    async def test_complete_sets_status_and_timestamp(self, user_id, spin_repo) -> None:
        """Completing a session sets status to COMPLETED with a timestamp."""
        chore_id = uuid.uuid4()
        session = _make_session(user_id, chore_id)
        spin_repo.get_by_id.return_value = session
        spin_repo.update.side_effect = lambda s: s

        command = CompleteSpinSessionCommand(spin_repo)
        await command.execute(CompleteSpinInput(user_id=user_id, session_id=session.id))

        assert session.status == SpinStatus.COMPLETED
        assert session.completed_at is not None
        spin_repo.update.assert_called_once_with(session)

    async def test_complete_raises_when_session_not_found(self, user_id, spin_repo) -> None:
        """Completing a nonexistent session raises EntityNotFoundError."""
        spin_repo.get_by_id.return_value = None

        command = CompleteSpinSessionCommand(spin_repo)
        with pytest.raises(EntityNotFoundError):
            await command.execute(
                CompleteSpinInput(user_id=user_id, session_id=uuid.uuid4())
            )

    async def test_complete_raises_for_wrong_user(self, user_id, other_user_id, spin_repo) -> None:
        """Completing another user's session raises AuthorizationError."""
        session = _make_session(other_user_id, uuid.uuid4())
        spin_repo.get_by_id.return_value = session

        command = CompleteSpinSessionCommand(spin_repo)
        with pytest.raises(AuthorizationError):
            await command.execute(CompleteSpinInput(user_id=user_id, session_id=session.id))

    async def test_complete_raises_when_not_pending(self, user_id, spin_repo) -> None:
        """Completing an already completed session raises ValidationError."""
        session = _make_session(user_id, uuid.uuid4(), status=SpinStatus.COMPLETED)
        spin_repo.get_by_id.return_value = session

        command = CompleteSpinSessionCommand(spin_repo)
        with pytest.raises(ValidationError):
            await command.execute(CompleteSpinInput(user_id=user_id, session_id=session.id))


class TestSkipSpinSessionCommand:
    """Test suite for SkipSpinSessionCommand."""

    async def test_skip_sets_status_and_timestamp(self, user_id, spin_repo) -> None:
        """Skipping a session sets status to SKIPPED with a timestamp."""
        chore_id = uuid.uuid4()
        session = _make_session(user_id, chore_id)
        spin_repo.get_by_id.return_value = session
        spin_repo.update.side_effect = lambda s: s

        command = SkipSpinSessionCommand(spin_repo)
        await command.execute(SkipSpinInput(user_id=user_id, session_id=session.id))

        assert session.status == SpinStatus.SKIPPED
        assert session.completed_at is not None

    async def test_skip_raises_when_session_not_found(self, user_id, spin_repo) -> None:
        """Skipping a nonexistent session raises EntityNotFoundError."""
        spin_repo.get_by_id.return_value = None

        command = SkipSpinSessionCommand(spin_repo)
        with pytest.raises(EntityNotFoundError):
            await command.execute(
                SkipSpinInput(user_id=user_id, session_id=uuid.uuid4())
            )

    async def test_skip_raises_for_wrong_user(self, user_id, other_user_id, spin_repo) -> None:
        """Skipping another user's session raises AuthorizationError."""
        session = _make_session(other_user_id, uuid.uuid4())
        spin_repo.get_by_id.return_value = session

        command = SkipSpinSessionCommand(spin_repo)
        with pytest.raises(AuthorizationError):
            await command.execute(SkipSpinInput(user_id=user_id, session_id=session.id))

    async def test_skip_raises_when_not_pending(self, user_id, spin_repo) -> None:
        """Skipping an already skipped session raises ValidationError."""
        session = _make_session(user_id, uuid.uuid4(), status=SpinStatus.SKIPPED)
        spin_repo.get_by_id.return_value = session

        command = SkipSpinSessionCommand(spin_repo)
        with pytest.raises(ValidationError):
            await command.execute(SkipSpinInput(user_id=user_id, session_id=session.id))


class TestQuickCompleteChoreCommand:
    """Test suite for QuickCompleteChoreCommand."""

    async def test_creates_completed_session(self, user_id, chore_repo, spin_repo) -> None:
        """Quick complete creates a spin session with COMPLETED status."""
        chore = _make_chore(user_id, name="Dishes")
        chore_repo.get_by_id.return_value = chore
        spin_repo.get_completed_counts_for_date.return_value = {}
        spin_repo.add.side_effect = lambda s: s

        command = QuickCompleteChoreCommand(chore_repo, spin_repo, tz_name="UTC")
        await command.execute(QuickCompleteChoreInput(user_id=user_id, chore_id=chore.id))

        added_session = spin_repo.add.call_args[0][0]
        assert added_session.status == SpinStatus.COMPLETED
        assert added_session.chore_name == "Dishes"
        assert added_session.completed_at is not None
        assert added_session.user_id == user_id

    async def test_raises_when_chore_not_found(self, user_id, chore_repo, spin_repo) -> None:
        """Quick complete raises EntityNotFoundError for nonexistent chore."""
        chore_repo.get_by_id.return_value = None

        command = QuickCompleteChoreCommand(chore_repo, spin_repo, tz_name="UTC")
        with pytest.raises(EntityNotFoundError):
            await command.execute(
                QuickCompleteChoreInput(user_id=user_id, chore_id=uuid.uuid4())
            )

    async def test_raises_for_wrong_user(self, user_id, other_user_id, chore_repo, spin_repo) -> None:
        """Quick complete raises AuthorizationError for another user's chore."""
        chore = _make_chore(other_user_id)
        chore_repo.get_by_id.return_value = chore

        command = QuickCompleteChoreCommand(chore_repo, spin_repo, tz_name="UTC")
        with pytest.raises(AuthorizationError):
            await command.execute(QuickCompleteChoreInput(user_id=user_id, chore_id=chore.id))

    async def test_raises_when_multiplicity_exceeded(self, user_id, chore_repo, spin_repo) -> None:
        """Quick complete raises ValidationError when daily multiplicity is reached."""
        chore = _make_chore(user_id, multiplicity=1)
        chore_repo.get_by_id.return_value = chore
        spin_repo.get_completed_counts_for_date.return_value = {chore.id: 1}

        command = QuickCompleteChoreCommand(chore_repo, spin_repo, tz_name="UTC")
        with pytest.raises(ValidationError):
            await command.execute(QuickCompleteChoreInput(user_id=user_id, chore_id=chore.id))


class TestQuickSkipChoreCommand:
    """Test suite for QuickSkipChoreCommand."""

    async def test_creates_skipped_session(self, user_id, chore_repo, spin_repo) -> None:
        """Quick skip creates a spin session with SKIPPED status."""
        chore = _make_chore(user_id, name="Laundry")
        chore_repo.get_by_id.return_value = chore
        spin_repo.add.side_effect = lambda s: s

        command = QuickSkipChoreCommand(chore_repo, spin_repo)
        await command.execute(QuickSkipChoreInput(user_id=user_id, chore_id=chore.id))

        added_session = spin_repo.add.call_args[0][0]
        assert added_session.status == SpinStatus.SKIPPED
        assert added_session.chore_name == "Laundry"
        assert added_session.completed_at is not None

    async def test_raises_when_chore_not_found(self, user_id, chore_repo, spin_repo) -> None:
        """Quick skip raises EntityNotFoundError for nonexistent chore."""
        chore_repo.get_by_id.return_value = None

        command = QuickSkipChoreCommand(chore_repo, spin_repo)
        with pytest.raises(EntityNotFoundError):
            await command.execute(
                QuickSkipChoreInput(user_id=user_id, chore_id=uuid.uuid4())
            )

    async def test_raises_for_wrong_user(self, user_id, other_user_id, chore_repo, spin_repo) -> None:
        """Quick skip raises AuthorizationError for another user's chore."""
        chore = _make_chore(other_user_id)
        chore_repo.get_by_id.return_value = chore

        command = QuickSkipChoreCommand(chore_repo, spin_repo)
        with pytest.raises(AuthorizationError):
            await command.execute(QuickSkipChoreInput(user_id=user_id, chore_id=chore.id))


class TestQuickDeactivateChoreCommand:
    """Test suite for QuickDeactivateChoreCommand."""

    async def test_creates_deactivated_session(self, user_id, chore_repo, spin_repo) -> None:
        """Quick deactivate creates a spin session with DEACTIVATED status."""
        chore = _make_chore(user_id, name="Vacuum")
        chore_repo.get_by_id.return_value = chore
        spin_repo.get_completed_counts_for_date.return_value = {}
        spin_repo.add.side_effect = lambda s: s

        command = QuickDeactivateChoreCommand(chore_repo, spin_repo, tz_name="UTC")
        await command.execute(QuickDeactivateChoreInput(user_id=user_id, chore_id=chore.id))

        added_session = spin_repo.add.call_args[0][0]
        assert added_session.status == SpinStatus.DEACTIVATED
        assert added_session.chore_name == "Vacuum"
        assert added_session.completed_at is not None
        assert added_session.user_id == user_id

    async def test_raises_when_chore_not_found(self, user_id, chore_repo, spin_repo) -> None:
        """Quick deactivate raises EntityNotFoundError for nonexistent chore."""
        chore_repo.get_by_id.return_value = None

        command = QuickDeactivateChoreCommand(chore_repo, spin_repo, tz_name="UTC")
        with pytest.raises(EntityNotFoundError):
            await command.execute(
                QuickDeactivateChoreInput(user_id=user_id, chore_id=uuid.uuid4())
            )

    async def test_raises_for_wrong_user(self, user_id, other_user_id, chore_repo, spin_repo) -> None:
        """Quick deactivate raises AuthorizationError for another user's chore."""
        chore = _make_chore(other_user_id)
        chore_repo.get_by_id.return_value = chore

        command = QuickDeactivateChoreCommand(chore_repo, spin_repo, tz_name="UTC")
        with pytest.raises(AuthorizationError):
            await command.execute(QuickDeactivateChoreInput(user_id=user_id, chore_id=chore.id))

    async def test_raises_when_multiplicity_exceeded(self, user_id, chore_repo, spin_repo) -> None:
        """Quick deactivate raises ValidationError when daily multiplicity is reached."""
        chore = _make_chore(user_id, multiplicity=1)
        chore_repo.get_by_id.return_value = chore
        spin_repo.get_completed_counts_for_date.return_value = {chore.id: 1}

        command = QuickDeactivateChoreCommand(chore_repo, spin_repo, tz_name="UTC")
        with pytest.raises(ValidationError):
            await command.execute(QuickDeactivateChoreInput(user_id=user_id, chore_id=chore.id))


class TestResetChoreCommand:
    """Test suite for ResetChoreCommand."""

    async def test_delegates_to_repository(self, user_id, spin_repo) -> None:
        """Reset chore deletes sessions for the specific chore today."""
        chore_id = uuid.uuid4()
        spin_repo.delete_for_chore_on_date.return_value = 2

        command = ResetChoreCommand(spin_repo, tz_name="UTC")
        result = await command.execute(ResetChoreInput(user_id=user_id, chore_id=chore_id))

        assert result == 2
        spin_repo.delete_for_chore_on_date.assert_called_once()
        call_args = spin_repo.delete_for_chore_on_date.call_args[0]
        assert call_args[0] == user_id
        assert call_args[1] == chore_id


class TestResetDailyWheelCommand:
    """Test suite for ResetDailyWheelCommand."""

    async def test_delegates_to_repository(self, user_id, spin_repo) -> None:
        """Reset daily deletes all sessions for today."""
        spin_repo.delete_for_date.return_value = 5

        command = ResetDailyWheelCommand(spin_repo, tz_name="UTC")
        result = await command.execute(ResetDailyWheelInput(user_id=user_id))

        assert result == 5
        spin_repo.delete_for_date.assert_called_once()
