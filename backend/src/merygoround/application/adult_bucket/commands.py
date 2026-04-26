"""Command use cases for the Adult Bucket bounded context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from merygoround.application.adult_bucket.dtos import (
    BucketItemResponse,
    BucketSettingsResponse,
)
from merygoround.application.shared.use_case import BaseCommand
from merygoround.domain.adult_bucket.entities import (
    DEFAULT_MAX_IN_PROGRESS,
    BucketItem,
    BucketKind,
    BucketSettings,
    KanbanStatus,
)
from merygoround.domain.adult_bucket.exceptions import BucketItemNotFoundError
from merygoround.domain.shared.exceptions import AuthorizationError

if TYPE_CHECKING:
    import uuid

    from merygoround.application.adult_bucket.dtos import (
        CreateBucketItemRequest,
        MoveBucketItemRequest,
        UpdateBucketItemRequest,
        UpdateBucketSettingsRequest,
    )
    from merygoround.domain.adult_bucket.repository import (
        BucketItemRepository,
        BucketSettingsRepository,
    )
    from merygoround.domain.adult_bucket.services import (
        BucketKanbanService,
        BucketSettingsService,
    )


def _item_to_response(item: BucketItem) -> BucketItemResponse:
    """Convert a BucketItem domain entity to a BucketItemResponse DTO."""
    return BucketItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        category=item.category,
        status=item.status.value,  # type: ignore[arg-type]
        kind=item.kind.value,  # type: ignore[arg-type]
        started_at=item.started_at,
        completed_at=item.completed_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@dataclass
class CreateBucketItemInput:
    """Input for CreateBucketItemCommand."""

    user_id: uuid.UUID
    kind: BucketKind
    request: CreateBucketItemRequest


@dataclass
class UpdateBucketItemInput:
    """Input for UpdateBucketItemCommand."""

    user_id: uuid.UUID
    kind: BucketKind
    item_id: uuid.UUID
    request: UpdateBucketItemRequest


@dataclass
class DeleteBucketItemInput:
    """Input for DeleteBucketItemCommand."""

    user_id: uuid.UUID
    kind: BucketKind
    item_id: uuid.UUID


@dataclass
class MoveBucketItemInput:
    """Input for MoveBucketItemCommand."""

    user_id: uuid.UUID
    kind: BucketKind
    item_id: uuid.UUID
    request: MoveBucketItemRequest


@dataclass
class UpdateBucketSettingsInput:
    """Input for UpdateBucketSettingsCommand."""

    user_id: uuid.UUID
    kind: BucketKind
    request: UpdateBucketSettingsRequest


def _ensure_owner_and_kind(
    item: BucketItem | None, user_id: uuid.UUID, kind: BucketKind, item_id: uuid.UUID
) -> BucketItem:
    """Raise the right exception if the item is missing or off-board.

    Items from another kind are surfaced as 404 (BucketItemNotFoundError) to avoid
    leaking the existence of items belonging to a different board for the same user.
    """
    if item is None or item.kind != kind:
        raise BucketItemNotFoundError(str(item_id))
    if item.user_id != user_id:
        raise AuthorizationError("You do not own this bucket item")
    return item


class CreateBucketItemCommand(BaseCommand[CreateBucketItemInput, BucketItemResponse]):
    """Creates a new bucket item for the authenticated user on the given board."""

    def __init__(self, item_repo: BucketItemRepository) -> None:
        self._item_repo = item_repo

    async def execute(self, input_data: CreateBucketItemInput) -> BucketItemResponse:
        req = input_data.request
        item = BucketItem(
            user_id=input_data.user_id,
            name=req.name,
            description=req.description,
            category=req.category,
            status=KanbanStatus.TO_DO,
            kind=input_data.kind,
        )
        item = await self._item_repo.add(item)
        return _item_to_response(item)


class UpdateBucketItemCommand(BaseCommand[UpdateBucketItemInput, BucketItemResponse]):
    """Updates an existing bucket item's editable fields."""

    def __init__(self, item_repo: BucketItemRepository) -> None:
        self._item_repo = item_repo

    async def execute(self, input_data: UpdateBucketItemInput) -> BucketItemResponse:
        item = _ensure_owner_and_kind(
            await self._item_repo.get_by_id(input_data.item_id),
            input_data.user_id,
            input_data.kind,
            input_data.item_id,
        )
        req = input_data.request
        if req.name is not None:
            item.name = req.name
        if req.description is not None:
            item.description = req.description
        if req.category is not None:
            item.category = req.category

        item.updated_at = datetime.now(UTC)
        item = await self._item_repo.update(item)
        return _item_to_response(item)


class DeleteBucketItemCommand(BaseCommand[DeleteBucketItemInput, None]):
    """Deletes an existing bucket item."""

    def __init__(self, item_repo: BucketItemRepository) -> None:
        self._item_repo = item_repo

    async def execute(self, input_data: DeleteBucketItemInput) -> None:
        _ensure_owner_and_kind(
            await self._item_repo.get_by_id(input_data.item_id),
            input_data.user_id,
            input_data.kind,
            input_data.item_id,
        )
        await self._item_repo.delete(input_data.item_id)


class MoveBucketItemCommand(BaseCommand[MoveBucketItemInput, BucketItemResponse]):
    """Moves a bucket item to a different Kanban column on the given board."""

    def __init__(
        self,
        item_repo: BucketItemRepository,
        settings_repo: BucketSettingsRepository,
        kanban_service: BucketKanbanService,
    ) -> None:
        self._item_repo = item_repo
        self._settings_repo = settings_repo
        self._kanban_service = kanban_service

    async def execute(self, input_data: MoveBucketItemInput) -> BucketItemResponse:
        item = _ensure_owner_and_kind(
            await self._item_repo.get_by_id(input_data.item_id),
            input_data.user_id,
            input_data.kind,
            input_data.item_id,
        )
        new_status = KanbanStatus(input_data.request.status)

        settings = await self._settings_repo.get_by_user_and_kind(
            input_data.user_id, input_data.kind
        )
        max_in_progress = (
            settings.max_in_progress if settings is not None else DEFAULT_MAX_IN_PROGRESS
        )

        in_progress_count = await self._item_repo.count_in_progress(
            input_data.user_id, input_data.kind
        )
        if item.status == KanbanStatus.IN_PROGRESS:
            in_progress_count = max(in_progress_count - 1, 0)

        item = self._kanban_service.move(
            item,
            new_status=new_status,
            in_progress_count=in_progress_count,
            max_in_progress=max_in_progress,
        )
        item = await self._item_repo.update(item)
        return _item_to_response(item)


class UpdateBucketSettingsCommand(
    BaseCommand[UpdateBucketSettingsInput, BucketSettingsResponse]
):
    """Updates the per-user-and-kind Kanban settings."""

    def __init__(
        self,
        settings_repo: BucketSettingsRepository,
        settings_service: BucketSettingsService,
    ) -> None:
        self._settings_repo = settings_repo
        self._settings_service = settings_service

    async def execute(
        self, input_data: UpdateBucketSettingsInput
    ) -> BucketSettingsResponse:
        max_in_progress = self._settings_service.validate_max_in_progress(
            input_data.request.max_in_progress
        )

        settings = await self._settings_repo.get_by_user_and_kind(
            input_data.user_id, input_data.kind
        )
        if settings is None:
            settings = BucketSettings(
                user_id=input_data.user_id,
                kind=input_data.kind,
                max_in_progress=max_in_progress,
            )
        else:
            settings.max_in_progress = max_in_progress
            settings.updated_at = datetime.now(UTC)

        settings = await self._settings_repo.upsert(settings)
        return BucketSettingsResponse(max_in_progress=settings.max_in_progress)
