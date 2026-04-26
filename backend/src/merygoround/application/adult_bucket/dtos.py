"""Data transfer objects for the Adult Bucket application layer."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

KanbanStatusLiteral = Literal["to_do", "in_progress", "blocked", "done"]
BucketKindLiteral = Literal["adult", "happy"]


class CreateBucketItemRequest(BaseModel):
    """Request DTO for creating a new bucket item.

    Attributes:
        name: Display name of the bucket item.
        description: Detailed description.
        category: Optional category label.
    """

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str | None = None


class UpdateBucketItemRequest(BaseModel):
    """Request DTO for updating an existing bucket item.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: Display name.
        description: Detailed description.
        category: Category label.
    """

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = None


class MoveBucketItemRequest(BaseModel):
    """Request DTO for moving a bucket item between Kanban columns.

    Attributes:
        status: Destination Kanban status.
    """

    status: KanbanStatusLiteral


class BucketItemResponse(BaseModel):
    """Response DTO representing a bucket item.

    Attributes:
        id: Bucket item unique identifier.
        name: Display name.
        description: Detailed description.
        category: Category label (if any).
        status: Current Kanban column.
        started_at: First time the item entered IN_PROGRESS, if ever.
        completed_at: First time the item entered DONE, if ever.
        created_at: Creation timestamp.
        updated_at: Last modification timestamp.
    """

    id: uuid.UUID
    name: str
    description: str
    category: str | None
    status: KanbanStatusLiteral
    kind: BucketKindLiteral
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DrawSuggestionResponse(BaseModel):
    """Response DTO for a random TO_DO suggestion (read-only, no state change).

    Attributes:
        item: The suggested bucket item.
    """

    item: BucketItemResponse


class BucketSettingsResponse(BaseModel):
    """Response DTO representing the per-user Kanban settings.

    Attributes:
        max_in_progress: Maximum allowed items in IN_PROGRESS at the same time.
    """

    max_in_progress: int


class UpdateBucketSettingsRequest(BaseModel):
    """Request DTO for updating per-user Kanban settings.

    Attributes:
        max_in_progress: Maximum allowed items in IN_PROGRESS (>= 1).
    """

    max_in_progress: int = Field(ge=1, le=99)
