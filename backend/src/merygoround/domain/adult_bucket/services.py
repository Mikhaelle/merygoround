"""Domain services for the Adult Bucket bounded context."""

from __future__ import annotations

import random
from datetime import UTC, datetime

from merygoround.domain.adult_bucket.entities import BucketItem, KanbanStatus
from merygoround.domain.adult_bucket.exceptions import (
    InvalidMaxInProgressError,
    MaxInProgressReachedError,
    NoBucketItemsError,
)


class BucketKanbanService:
    """Pure domain service implementing the Kanban board rules.

    Enforces a per-user maximum of items in IN_PROGRESS but otherwise allows free
    movement between columns (TO_DO, IN_PROGRESS, BLOCKED, DONE).
    """

    def move(
        self,
        item: BucketItem,
        new_status: KanbanStatus,
        in_progress_count: int,
        max_in_progress: int,
    ) -> BucketItem:
        """Transition a bucket item to a new Kanban column.

        Args:
            item: The BucketItem to move.
            new_status: Destination Kanban column.
            in_progress_count: Current count of IN_PROGRESS items for the user
                (excluding the item being moved).
            max_in_progress: Configured per-user maximum for IN_PROGRESS.

        Returns:
            The mutated BucketItem with the new status and timestamps.

        Raises:
            MaxInProgressReachedError: If moving into IN_PROGRESS would exceed the
                configured limit.
        """
        if (
            new_status == KanbanStatus.IN_PROGRESS
            and item.status != KanbanStatus.IN_PROGRESS
            and in_progress_count >= max_in_progress
        ):
            raise MaxInProgressReachedError(max_in_progress)

        now = datetime.now(UTC)

        if new_status == KanbanStatus.IN_PROGRESS and item.started_at is None:
            item.started_at = now
        if new_status == KanbanStatus.DONE and item.completed_at is None:
            item.completed_at = now

        item.status = new_status
        item.updated_at = now
        return item

    def draw_suggestion(
        self,
        to_do_items: list[BucketItem],
        in_progress_count: int,
        max_in_progress: int,
    ) -> BucketItem:
        """Pick a random TO_DO item to suggest to the user.

        Does not mutate any state. Caller may then move the item via ``move``.

        Args:
            to_do_items: All items currently in the TO_DO column.
            in_progress_count: Current count of IN_PROGRESS items for the user.
            max_in_progress: Configured per-user maximum for IN_PROGRESS.

        Returns:
            A randomly selected BucketItem from the TO_DO list.

        Raises:
            MaxInProgressReachedError: If the user already has the maximum
                allowed items in progress (no point suggesting a new draw).
            NoBucketItemsError: If there are no TO_DO items to suggest.
        """
        if in_progress_count >= max_in_progress:
            raise MaxInProgressReachedError(max_in_progress)
        if not to_do_items:
            raise NoBucketItemsError()
        return random.choice(to_do_items)


class BucketSettingsService:
    """Pure domain service that validates BucketSettings invariants."""

    def validate_max_in_progress(self, value: int) -> int:
        """Ensure ``max_in_progress`` is a positive integer.

        Args:
            value: Candidate maximum value.

        Returns:
            The validated integer.

        Raises:
            InvalidMaxInProgressError: If ``value`` is not a positive integer.
        """
        if not isinstance(value, int) or value < 1:
            raise InvalidMaxInProgressError()
        return value
