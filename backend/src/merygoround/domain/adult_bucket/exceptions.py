"""Domain exceptions for the Adult Bucket bounded context."""

from __future__ import annotations

from merygoround.domain.shared.exceptions import DomainException


class NoBucketItemsError(DomainException):
    """Raised when no eligible bucket items are available for a draw suggestion."""

    def __init__(self) -> None:
        super().__init__("No bucket items available for drawing.")


class MaxInProgressReachedError(DomainException):
    """Raised when moving an item to IN_PROGRESS would exceed the per-user limit.

    Args:
        max_in_progress: The configured maximum number of IN_PROGRESS items.
    """

    def __init__(self, max_in_progress: int) -> None:
        super().__init__(
            f"Maximum of {max_in_progress} in-progress items already reached."
        )
        self.max_in_progress = max_in_progress


class InvalidMaxInProgressError(DomainException):
    """Raised when an invalid max_in_progress value is provided."""

    def __init__(self) -> None:
        super().__init__("max_in_progress must be a positive integer.")


class BucketItemNotFoundError(DomainException):
    """Raised when a bucket item cannot be found.

    Args:
        item_id: The identifier used in the lookup.
    """

    def __init__(self, item_id: str = "") -> None:
        msg = f"Bucket item not found: '{item_id}'" if item_id else "Bucket item not found"
        super().__init__(msg)
