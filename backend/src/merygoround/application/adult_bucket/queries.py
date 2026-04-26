"""Query use cases for the Adult Bucket bounded context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from merygoround.application.adult_bucket.dtos import (
    BucketItemResponse,
    BucketSettingsResponse,
    DrawSuggestionResponse,
)
from merygoround.application.shared.use_case import BaseQuery
from merygoround.domain.adult_bucket.entities import DEFAULT_MAX_IN_PROGRESS, BucketKind

if TYPE_CHECKING:
    import uuid

    from merygoround.domain.adult_bucket.entities import BucketItem
    from merygoround.domain.adult_bucket.repository import (
        BucketItemRepository,
        BucketSettingsRepository,
    )
    from merygoround.domain.adult_bucket.services import BucketKanbanService


def _item_to_response(item: BucketItem) -> BucketItemResponse:
    """Convert a BucketItem entity to a BucketItemResponse DTO."""
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
class BucketBoardQueryInput:
    """Input for queries scoped to a single user/kind board."""

    user_id: uuid.UUID
    kind: BucketKind


class ListBucketItemsQuery(BaseQuery[BucketBoardQueryInput, list[BucketItemResponse]]):
    """Retrieves all bucket items for the authenticated user on a given board."""

    def __init__(self, item_repo: BucketItemRepository) -> None:
        self._item_repo = item_repo

    async def execute(
        self, input_data: BucketBoardQueryInput
    ) -> list[BucketItemResponse]:
        items = await self._item_repo.get_by_user_and_kind(
            input_data.user_id, input_data.kind
        )
        return [_item_to_response(item) for item in items]


class GetBucketSettingsQuery(BaseQuery[BucketBoardQueryInput, BucketSettingsResponse]):
    """Retrieves the Kanban settings for the user on a given board."""

    def __init__(self, settings_repo: BucketSettingsRepository) -> None:
        self._settings_repo = settings_repo

    async def execute(
        self, input_data: BucketBoardQueryInput
    ) -> BucketSettingsResponse:
        settings = await self._settings_repo.get_by_user_and_kind(
            input_data.user_id, input_data.kind
        )
        max_in_progress = (
            settings.max_in_progress if settings is not None else DEFAULT_MAX_IN_PROGRESS
        )
        return BucketSettingsResponse(max_in_progress=max_in_progress)


class DrawSuggestionQuery(BaseQuery[BucketBoardQueryInput, DrawSuggestionResponse]):
    """Suggests a random TO_DO item for the given board (no state change)."""

    def __init__(
        self,
        item_repo: BucketItemRepository,
        settings_repo: BucketSettingsRepository,
        kanban_service: BucketKanbanService,
    ) -> None:
        self._item_repo = item_repo
        self._settings_repo = settings_repo
        self._kanban_service = kanban_service

    async def execute(
        self, input_data: BucketBoardQueryInput
    ) -> DrawSuggestionResponse:
        settings = await self._settings_repo.get_by_user_and_kind(
            input_data.user_id, input_data.kind
        )
        max_in_progress = (
            settings.max_in_progress if settings is not None else DEFAULT_MAX_IN_PROGRESS
        )

        in_progress_count = await self._item_repo.count_in_progress(
            input_data.user_id, input_data.kind
        )
        to_do_items = await self._item_repo.get_to_do_for_user_and_kind(
            input_data.user_id, input_data.kind
        )

        suggestion = self._kanban_service.draw_suggestion(
            to_do_items=to_do_items,
            in_progress_count=in_progress_count,
            max_in_progress=max_in_progress,
        )
        return DrawSuggestionResponse(item=_item_to_response(suggestion))
