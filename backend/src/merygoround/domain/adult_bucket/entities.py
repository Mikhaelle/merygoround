"""Entities and value objects for the Adult Bucket bounded context."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from merygoround.domain.shared.entity import AggregateRoot


class KanbanStatus(enum.Enum):
    """Kanban column where a bucket item currently lives."""

    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class BucketKind(enum.Enum):
    """Distinguishes which user-facing board a bucket item belongs to.

    'adult' is the original Adult Bucket (life admin tasks).
    'happy' is the Balde Feliz (lighter / fun tasks) introduced later.
    """

    ADULT = "adult"
    HAPPY = "happy"


DEFAULT_MAX_IN_PROGRESS = 2


@dataclass
class BucketItem(AggregateRoot):
    """Represents an adult life task on the Kanban board.

    Args:
        id: Unique identifier.
        user_id: Owner of the bucket item.
        name: Display name of the task.
        description: Detailed description of the task.
        category: Optional categorization label.
        status: Kanban column the item currently belongs to.
        started_at: Timestamp the item entered IN_PROGRESS for the first time.
        completed_at: Timestamp the item entered DONE for the first time.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last modification.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    description: str = ""
    category: str | None = None
    status: KanbanStatus = KanbanStatus.TO_DO
    kind: BucketKind = BucketKind.ADULT
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BucketSettings(AggregateRoot):
    """Per-user Kanban settings.

    Args:
        id: Unique identifier.
        user_id: Owner of the settings.
        max_in_progress: Maximum number of items allowed in IN_PROGRESS at once.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last modification.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    kind: BucketKind = BucketKind.ADULT
    max_in_progress: int = DEFAULT_MAX_IN_PROGRESS
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
