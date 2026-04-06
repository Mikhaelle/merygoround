"""Entities for the Wheel bounded context."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from merygoround.domain.shared.entity import Entity


class SpinStatus(enum.Enum):
    """Status of a spin session."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    DEACTIVATED = "DEACTIVATED"


@dataclass
class SpinSession(Entity):
    """Records the result of a single wheel spin.

    Args:
        id: Unique identifier.
        user_id: The user who performed the spin.
        selected_chore_id: The chore that was selected.
        chore_name: Snapshot of the chore name at spin time.
        spun_at: Timestamp of the spin.
        completed_at: Timestamp when the chore was completed (if applicable).
        status: Current status of the spin session.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    selected_chore_id: uuid.UUID = field(default_factory=uuid.uuid4)
    chore_name: str = ""
    spun_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    status: SpinStatus = SpinStatus.PENDING
