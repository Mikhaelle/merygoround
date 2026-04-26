"""Repository interfaces for the Adult Bucket bounded context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from merygoround.domain.adult_bucket.entities import (
        BucketItem,
        BucketKind,
        BucketSettings,
        KanbanStatus,
    )


class BucketItemRepository(ABC):
    """Abstract repository for BucketItem aggregate persistence.

    All listing queries are scoped by ``(user_id, kind)`` so the same table can
    host multiple Kanban boards (e.g. 'adult' and 'happy') for the same user.
    """

    @abstractmethod
    async def get_by_id(self, item_id: uuid.UUID) -> BucketItem | None:
        """Retrieve a bucket item by its unique identifier (no kind filter)."""

    @abstractmethod
    async def get_by_user_and_kind(
        self, user_id: uuid.UUID, kind: BucketKind
    ) -> list[BucketItem]:
        """Retrieve all bucket items belonging to ``user_id`` for the given kind."""

    @abstractmethod
    async def count_in_progress(self, user_id: uuid.UUID, kind: BucketKind) -> int:
        """Count IN_PROGRESS items for a user on a given board."""

    @abstractmethod
    async def get_to_do_for_user_and_kind(
        self, user_id: uuid.UUID, kind: BucketKind
    ) -> list[BucketItem]:
        """Retrieve all TO_DO items for the user on the given board."""

    @abstractmethod
    async def add(self, item: BucketItem) -> BucketItem:
        """Persist a new bucket item."""

    @abstractmethod
    async def update(self, item: BucketItem) -> BucketItem:
        """Update an existing bucket item."""

    @abstractmethod
    async def delete(self, item_id: uuid.UUID) -> None:
        """Remove a bucket item by its unique identifier."""


class BucketSettingsRepository(ABC):
    """Abstract repository for per-user-and-kind BucketSettings persistence."""

    @abstractmethod
    async def get_by_user_and_kind(
        self, user_id: uuid.UUID, kind: BucketKind
    ) -> BucketSettings | None:
        """Retrieve the settings for a user on a given board, if persisted."""

    @abstractmethod
    async def upsert(self, settings: BucketSettings) -> BucketSettings:
        """Insert or update the settings for a user-and-kind tuple."""
