"""Bucket API routes (Kanban board, parameterized by board kind)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from merygoround.api.dependencies import get_current_user, get_session
from merygoround.application.adult_bucket.commands import (
    CreateBucketItemCommand,
    CreateBucketItemInput,
    DeleteBucketItemCommand,
    DeleteBucketItemInput,
    MoveBucketItemCommand,
    MoveBucketItemInput,
    TransferBucketItemCommand,
    TransferBucketItemInput,
    UpdateBucketItemCommand,
    UpdateBucketItemInput,
    UpdateBucketSettingsCommand,
    UpdateBucketSettingsInput,
)
from merygoround.application.adult_bucket.dtos import (
    BucketItemResponse,
    BucketKindLiteral,
    BucketSettingsResponse,
    CreateBucketItemRequest,
    DrawSuggestionResponse,
    MoveBucketItemRequest,
    TransferBucketItemRequest,
    UpdateBucketItemRequest,
    UpdateBucketSettingsRequest,
)
from merygoround.application.adult_bucket.queries import (
    BucketBoardQueryInput,
    DrawSuggestionQuery,
    GetBucketSettingsQuery,
    ListBucketItemsQuery,
)
from merygoround.domain.adult_bucket.entities import BucketKind
from merygoround.domain.adult_bucket.services import (
    BucketKanbanService,
    BucketSettingsService,
)
from merygoround.infrastructure.database.repositories.bucket_repository import (
    SqlAlchemyBucketItemRepository,
    SqlAlchemyBucketSettingsRepository,
)

router = APIRouter(prefix="/bucket", tags=["adult-bucket"])

_KindPath = Annotated[BucketKindLiteral, Path(description="Board kind: adult or happy")]


def _to_kind(kind: BucketKindLiteral) -> BucketKind:
    """Convert a kind path string into the domain enum."""
    return BucketKind(kind)


@router.get("/{kind}/items", response_model=list[BucketItemResponse])
async def list_items(
    kind: _KindPath,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[BucketItemResponse]:
    """List all items on the given board for the authenticated user."""
    repo = SqlAlchemyBucketItemRepository(session)
    query = ListBucketItemsQuery(repo)
    return await query.execute(
        BucketBoardQueryInput(user_id=user_id, kind=_to_kind(kind))
    )


@router.post("/{kind}/items", response_model=BucketItemResponse, status_code=201)
async def create_item(
    kind: _KindPath,
    body: CreateBucketItemRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BucketItemResponse:
    """Create a new item on the given board (lands in TO_DO)."""
    repo = SqlAlchemyBucketItemRepository(session)
    command = CreateBucketItemCommand(repo)
    return await command.execute(
        CreateBucketItemInput(user_id=user_id, kind=_to_kind(kind), request=body)
    )


@router.put("/{kind}/items/{item_id}", response_model=BucketItemResponse)
async def update_item(
    kind: _KindPath,
    item_id: uuid.UUID,
    body: UpdateBucketItemRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BucketItemResponse:
    """Update an item's editable fields on the given board."""
    repo = SqlAlchemyBucketItemRepository(session)
    command = UpdateBucketItemCommand(repo)
    return await command.execute(
        UpdateBucketItemInput(
            user_id=user_id,
            kind=_to_kind(kind),
            item_id=item_id,
            request=body,
        )
    )


@router.delete("/{kind}/items/{item_id}", status_code=204)
async def delete_item(
    kind: _KindPath,
    item_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete an item from the given board."""
    repo = SqlAlchemyBucketItemRepository(session)
    command = DeleteBucketItemCommand(repo)
    await command.execute(
        DeleteBucketItemInput(user_id=user_id, kind=_to_kind(kind), item_id=item_id)
    )


@router.put("/{kind}/items/{item_id}/move", response_model=BucketItemResponse)
async def move_item(
    kind: _KindPath,
    item_id: uuid.UUID,
    body: MoveBucketItemRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BucketItemResponse:
    """Move an item between Kanban columns on the given board."""
    item_repo = SqlAlchemyBucketItemRepository(session)
    settings_repo = SqlAlchemyBucketSettingsRepository(session)
    command = MoveBucketItemCommand(item_repo, settings_repo, BucketKanbanService())
    return await command.execute(
        MoveBucketItemInput(
            user_id=user_id,
            kind=_to_kind(kind),
            item_id=item_id,
            request=body,
        )
    )


@router.put("/{kind}/items/{item_id}/transfer", response_model=BucketItemResponse)
async def transfer_item(
    kind: _KindPath,
    item_id: uuid.UUID,
    body: TransferBucketItemRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BucketItemResponse:
    """Transfer an item to a different board (adult <-> happy)."""
    item_repo = SqlAlchemyBucketItemRepository(session)
    settings_repo = SqlAlchemyBucketSettingsRepository(session)
    command = TransferBucketItemCommand(item_repo, settings_repo, BucketKanbanService())
    return await command.execute(
        TransferBucketItemInput(
            user_id=user_id,
            kind=_to_kind(kind),
            item_id=item_id,
            request=body,
        )
    )


@router.post("/{kind}/draw", response_model=DrawSuggestionResponse)
async def draw_suggestion(
    kind: _KindPath,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DrawSuggestionResponse:
    """Suggest a random TO_DO item on the given board (no state change)."""
    item_repo = SqlAlchemyBucketItemRepository(session)
    settings_repo = SqlAlchemyBucketSettingsRepository(session)
    query = DrawSuggestionQuery(item_repo, settings_repo, BucketKanbanService())
    return await query.execute(
        BucketBoardQueryInput(user_id=user_id, kind=_to_kind(kind))
    )


@router.get("/{kind}/settings", response_model=BucketSettingsResponse)
async def get_settings(
    kind: _KindPath,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BucketSettingsResponse:
    """Get the user's settings for the given board (default values if absent)."""
    settings_repo = SqlAlchemyBucketSettingsRepository(session)
    query = GetBucketSettingsQuery(settings_repo)
    return await query.execute(
        BucketBoardQueryInput(user_id=user_id, kind=_to_kind(kind))
    )


@router.put("/{kind}/settings", response_model=BucketSettingsResponse)
async def update_settings(
    kind: _KindPath,
    body: UpdateBucketSettingsRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BucketSettingsResponse:
    """Update the user's settings (max_in_progress) for the given board."""
    settings_repo = SqlAlchemyBucketSettingsRepository(session)
    command = UpdateBucketSettingsCommand(settings_repo, BucketSettingsService())
    return await command.execute(
        UpdateBucketSettingsInput(user_id=user_id, kind=_to_kind(kind), request=body)
    )
