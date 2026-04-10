"""Data transfer objects for the Chores application layer."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TimeWeightRuleDTO(BaseModel):
    """DTO for a time-based weight rule.

    Attributes:
        hour: Hour of the day (0-23).
        weight: Positive weight value up to 3.0.
    """

    hour: int = Field(ge=0, le=23)
    weight: float = Field(gt=0, le=3.0)


class WheelConfigDTO(BaseModel):
    """DTO for wheel configuration.

    Attributes:
        multiplicity: Number of wheel slots (>= 1).
        time_weight_rules: List of time-weight rules.
    """

    multiplicity: int = Field(ge=1, default=1)
    time_weight_rules: list[TimeWeightRuleDTO] = Field(default_factory=list)


class CreateChoreRequest(BaseModel):
    """Request DTO for creating a new chore.

    Attributes:
        name: Display name of the chore.
        estimated_duration_minutes: Duration in minutes (5 or 10).
        category: Optional category label.
        multiplicity: Wheel slot count (1-3, default 1).
        time_weight_rules: Optional time-weight rules.
        reward_value: BRL reward for completing the chore (R$0.01–R$10.00).
    """

    name: str = Field(min_length=1, max_length=200)
    estimated_duration_minutes: Literal[5, 10]
    category: str | None = None
    multiplicity: int = Field(ge=1, default=1)
    time_weight_rules: list[TimeWeightRuleDTO] = Field(default_factory=list)
    reward_value: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.01"), le=Decimal("10.00"))


class UpdateChoreRequest(BaseModel):
    """Request DTO for updating an existing chore.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: Display name of the chore.
        estimated_duration_minutes: Duration in minutes (5 or 10).
        category: Category label.
        multiplicity: Wheel slot count (1-3).
        time_weight_rules: Time-weight rules.
        reward_value: BRL reward for completing the chore (R$0.01–R$10.00).
    """

    name: str | None = Field(default=None, min_length=1, max_length=200)
    estimated_duration_minutes: Literal[5, 10] | None = None
    category: str | None = None
    multiplicity: int | None = Field(default=None, ge=1)
    time_weight_rules: list[TimeWeightRuleDTO] | None = None
    reward_value: Decimal | None = Field(default=None, ge=Decimal("0.01"), le=Decimal("10.00"))


class ChoreResponse(BaseModel):
    """Response DTO representing a chore.

    Attributes:
        id: Chore unique identifier.
        name: Display name.
        estimated_duration_minutes: Duration in minutes.
        category: Category label (if any).
        wheel_config: Wheel configuration.
        reward_value: BRL reward for completing the chore.
        created_at: Creation timestamp.
        updated_at: Last modification timestamp.
    """

    id: uuid.UUID
    name: str
    estimated_duration_minutes: int
    category: str | None
    wheel_config: WheelConfigDTO
    reward_value: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
