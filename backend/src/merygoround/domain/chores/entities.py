"""Entities for the Chores bounded context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from merygoround.domain.chores.value_objects import Duration, Multiplicity, RewardValue, REWARD_DEFAULT, TimeWeightRule
from merygoround.domain.shared.entity import AggregateRoot


@dataclass
class WheelConfiguration:
    """Configuration controlling how a chore appears and weights on the wheel.

    Args:
        multiplicity: Number of slots the chore occupies.
        time_weight_rules: Hour-specific weight overrides.
    """

    multiplicity: Multiplicity = field(default_factory=lambda: Multiplicity(1))
    time_weight_rules: list[TimeWeightRule] = field(default_factory=list)


@dataclass
class Chore(AggregateRoot):
    """Represents a household chore that can appear on the spinning wheel.

    Args:
        id: Unique identifier.
        user_id: Owner of the chore.
        name: Display name of the chore.
        estimated_duration: Duration value object (1-10 minutes).
        category: Optional categorization label.
        wheel_config: Wheel appearance and weighting configuration.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last modification.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    estimated_duration: Duration = field(default_factory=lambda: Duration(1))
    category: str | None = None
    wheel_config: WheelConfiguration = field(default_factory=WheelConfiguration)
    reward_value: RewardValue = field(default_factory=lambda: RewardValue(REWARD_DEFAULT))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
