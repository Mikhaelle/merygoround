"""Tests for the BucketKanbanService and BucketSettingsService domain services."""

from __future__ import annotations

import uuid

import pytest

from merygoround.domain.adult_bucket.entities import BucketItem, BucketKind, KanbanStatus
from merygoround.domain.adult_bucket.exceptions import (
    InvalidMaxInProgressError,
    MaxInProgressReachedError,
    NoBucketItemsError,
    SameKindTransferError,
)
from merygoround.domain.adult_bucket.services import (
    BucketKanbanService,
    BucketSettingsService,
)


@pytest.fixture
def kanban_service() -> BucketKanbanService:
    """Provide a BucketKanbanService instance."""
    return BucketKanbanService()


@pytest.fixture
def settings_service() -> BucketSettingsService:
    """Provide a BucketSettingsService instance."""
    return BucketSettingsService()


@pytest.fixture
def user_id() -> uuid.UUID:
    """Provide a fixed test user UUID."""
    return uuid.uuid4()


def _make_item(
    user_id: uuid.UUID,
    name: str = "Test Item",
    status: KanbanStatus = KanbanStatus.TO_DO,
) -> BucketItem:
    """Create a BucketItem in a given status for testing."""
    return BucketItem(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        description="A test bucket item",
        status=status,
    )


class TestBucketKanbanServiceMove:
    """Test suite for BucketKanbanService.move."""

    def test_move_to_in_progress_when_under_limit(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Moving an item into IN_PROGRESS while under the limit succeeds."""
        item = _make_item(user_id, status=KanbanStatus.TO_DO)

        result = kanban_service.move(
            item, KanbanStatus.IN_PROGRESS, in_progress_count=1, max_in_progress=2
        )

        assert result.status == KanbanStatus.IN_PROGRESS
        assert result.started_at is not None
        assert result.completed_at is None

    def test_move_to_in_progress_blocked_when_at_limit(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Moving into IN_PROGRESS at the limit raises MaxInProgressReachedError."""
        item = _make_item(user_id, status=KanbanStatus.TO_DO)

        with pytest.raises(MaxInProgressReachedError):
            kanban_service.move(
                item, KanbanStatus.IN_PROGRESS, in_progress_count=2, max_in_progress=2
            )

    def test_move_to_done_sets_completed_at(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Moving an item into DONE stamps completed_at."""
        item = _make_item(user_id, status=KanbanStatus.IN_PROGRESS)

        result = kanban_service.move(
            item, KanbanStatus.DONE, in_progress_count=0, max_in_progress=2
        )

        assert result.status == KanbanStatus.DONE
        assert result.completed_at is not None

    def test_move_done_to_in_progress_when_slot_free(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Done items can be reopened into IN_PROGRESS if there is a slot."""
        item = _make_item(user_id, status=KanbanStatus.DONE)

        result = kanban_service.move(
            item, KanbanStatus.IN_PROGRESS, in_progress_count=0, max_in_progress=2
        )

        assert result.status == KanbanStatus.IN_PROGRESS

    def test_move_in_progress_to_blocked_does_not_check_limit(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Moving away from IN_PROGRESS never raises the limit error."""
        item = _make_item(user_id, status=KanbanStatus.IN_PROGRESS)

        result = kanban_service.move(
            item, KanbanStatus.BLOCKED, in_progress_count=2, max_in_progress=2
        )

        assert result.status == KanbanStatus.BLOCKED

    def test_move_in_progress_to_in_progress_is_noop_for_limit(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Re-applying IN_PROGRESS to an already IN_PROGRESS item never raises."""
        item = _make_item(user_id, status=KanbanStatus.IN_PROGRESS)

        result = kanban_service.move(
            item, KanbanStatus.IN_PROGRESS, in_progress_count=2, max_in_progress=2
        )

        assert result.status == KanbanStatus.IN_PROGRESS

    def test_move_to_blocked_keeps_started_at(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """started_at is preserved when leaving IN_PROGRESS to BLOCKED."""
        item = _make_item(user_id, status=KanbanStatus.IN_PROGRESS)
        result = kanban_service.move(
            item, KanbanStatus.IN_PROGRESS, in_progress_count=0, max_in_progress=2
        )
        first_started = result.started_at

        result = kanban_service.move(
            result, KanbanStatus.BLOCKED, in_progress_count=0, max_in_progress=2
        )

        assert result.started_at == first_started


class TestBucketKanbanServiceTransfer:
    """Test suite for BucketKanbanService.transfer."""

    def test_transfer_changes_kind(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Transferring switches the item to the destination board."""
        item = _make_item(user_id, status=KanbanStatus.TO_DO)
        item.kind = BucketKind.ADULT

        result = kanban_service.transfer(
            item,
            target_kind=BucketKind.HAPPY,
            destination_in_progress_count=0,
            destination_max_in_progress=2,
        )

        assert result.kind == BucketKind.HAPPY

    def test_transfer_to_same_kind_raises(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Transferring to the same kind raises SameKindTransferError."""
        item = _make_item(user_id, status=KanbanStatus.TO_DO)
        item.kind = BucketKind.ADULT
        with pytest.raises(SameKindTransferError):
            kanban_service.transfer(
                item,
                target_kind=BucketKind.ADULT,
                destination_in_progress_count=0,
                destination_max_in_progress=2,
            )

    def test_transfer_in_progress_blocked_when_destination_full(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """An IN_PROGRESS item can't be transferred when the destination is full."""
        item = _make_item(user_id, status=KanbanStatus.IN_PROGRESS)
        item.kind = BucketKind.ADULT
        with pytest.raises(MaxInProgressReachedError):
            kanban_service.transfer(
                item,
                target_kind=BucketKind.HAPPY,
                destination_in_progress_count=2,
                destination_max_in_progress=2,
            )

    def test_transfer_keeps_status(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """Transferring preserves the item's status."""
        item = _make_item(user_id, status=KanbanStatus.BLOCKED)
        item.kind = BucketKind.ADULT
        result = kanban_service.transfer(
            item,
            target_kind=BucketKind.HAPPY,
            destination_in_progress_count=0,
            destination_max_in_progress=2,
        )
        assert result.status == KanbanStatus.BLOCKED


class TestBucketKanbanServiceDrawSuggestion:
    """Test suite for BucketKanbanService.draw_suggestion."""

    def test_draw_returns_random_to_do_item(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """draw_suggestion returns one of the TO_DO items without mutation."""
        items = [_make_item(user_id, f"Item {i}") for i in range(3)]

        suggestion = kanban_service.draw_suggestion(
            to_do_items=items, in_progress_count=0, max_in_progress=2
        )

        assert suggestion in items
        assert suggestion.status == KanbanStatus.TO_DO

    def test_draw_raises_when_at_max_in_progress(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """draw_suggestion raises when the user is already at max IN_PROGRESS."""
        items = [_make_item(user_id)]
        with pytest.raises(MaxInProgressReachedError):
            kanban_service.draw_suggestion(
                to_do_items=items, in_progress_count=2, max_in_progress=2
            )

    def test_draw_raises_when_no_to_do_items(
        self, kanban_service: BucketKanbanService, user_id: uuid.UUID
    ) -> None:
        """draw_suggestion raises NoBucketItemsError when TO_DO is empty."""
        with pytest.raises(NoBucketItemsError):
            kanban_service.draw_suggestion(
                to_do_items=[], in_progress_count=0, max_in_progress=2
            )


class TestBucketSettingsService:
    """Test suite for BucketSettingsService."""

    def test_validate_accepts_positive_int(
        self, settings_service: BucketSettingsService
    ) -> None:
        """A positive integer is accepted unchanged."""
        assert settings_service.validate_max_in_progress(3) == 3

    def test_validate_rejects_zero(
        self, settings_service: BucketSettingsService
    ) -> None:
        """Zero is rejected."""
        with pytest.raises(InvalidMaxInProgressError):
            settings_service.validate_max_in_progress(0)

    def test_validate_rejects_negative(
        self, settings_service: BucketSettingsService
    ) -> None:
        """Negative integers are rejected."""
        with pytest.raises(InvalidMaxInProgressError):
            settings_service.validate_max_in_progress(-1)

    def test_validate_rejects_non_int(
        self, settings_service: BucketSettingsService
    ) -> None:
        """Non-integer values are rejected."""
        with pytest.raises(InvalidMaxInProgressError):
            settings_service.validate_max_in_progress("3")  # type: ignore[arg-type]
