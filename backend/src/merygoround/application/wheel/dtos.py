"""Data transfer objects for the Wheel application layer."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from merygoround.application.chores.dtos import ChoreResponse


class SpinResultResponse(BaseModel):
    """Response DTO for a wheel spin result.

    Attributes:
        id: Spin session unique identifier.
        chore: The selected chore details.
        spun_at: Timestamp of the spin.
        status: Current status of the spin session.
    """

    id: uuid.UUID
    chore: ChoreResponse
    spun_at: datetime
    status: str


class WheelSegmentResponse(BaseModel):
    """Response DTO for a single wheel segment.

    Attributes:
        chore_id: ID of the chore.
        name: Display name of the chore.
        color: Hex color code for the segment.
        effective_weight: Calculated weight for the current hour.
    """

    chore_id: uuid.UUID
    name: str
    color: str
    effective_weight: float


class SpinHistoryItem(BaseModel):
    """Single entry in spin history.

    Attributes:
        id: Spin session unique identifier.
        chore_name: Name of the chore at spin time.
        spun_at: Timestamp of the spin.
        completed_at: Timestamp of completion (if applicable).
        status: Status of the spin session.
    """

    id: uuid.UUID
    chore_name: str
    spun_at: datetime
    completed_at: datetime | None
    status: str


class SpinHistoryResponse(BaseModel):
    """Response DTO for paginated spin history.

    Attributes:
        items: List of spin history entries.
        total: Total number of entries.
        page: Current page number.
        per_page: Number of entries per page.
    """

    items: list[SpinHistoryItem]
    total: int
    page: int
    per_page: int


class DailyProgressItem(BaseModel):
    """Daily progress for a single chore.

    Attributes:
        chore_id: ID of the chore.
        completed: Number of completions today.
        skipped: Number of skips today.
        deactivated: Number of deactivations today.
        multiplicity: Total multiplicity for the chore.
    """

    chore_id: uuid.UUID
    completed: int
    skipped: int
    deactivated: int
    multiplicity: int


class SpinHistoryQuery(BaseModel):
    """Input DTO for spin history pagination.

    Attributes:
        page: Page number (1-indexed).
        per_page: Items per page.
    """

    page: int = Field(ge=1, default=1)
    per_page: int = Field(ge=1, le=100, default=20)
