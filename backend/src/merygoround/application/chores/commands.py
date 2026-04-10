"""Command use cases for the Chores bounded context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from merygoround.application.chores.dtos import (
    ChoreResponse,
    CreateChoreRequest,
    TimeWeightRuleDTO,
    UpdateChoreRequest,
    WheelConfigDTO,
)
from merygoround.application.shared.use_case import BaseCommand
from merygoround.domain.chores.entities import Chore, WheelConfiguration
from merygoround.domain.chores.exceptions import ChoreNotFoundError
from merygoround.domain.chores.value_objects import Duration, Multiplicity, RewardValue, TimeWeightRule
from merygoround.domain.shared.exceptions import AuthorizationError

if TYPE_CHECKING:
    from merygoround.domain.chores.repository import ChoreRepository


@dataclass
class CreateChoreInput:
    """Input for CreateChoreCommand.

    Attributes:
        user_id: Owner of the new chore.
        request: Chore creation data.
    """

    user_id: uuid.UUID
    request: CreateChoreRequest


@dataclass
class UpdateChoreInput:
    """Input for UpdateChoreCommand.

    Attributes:
        user_id: Requesting user.
        chore_id: ID of the chore to update.
        request: Chore update data.
    """

    user_id: uuid.UUID
    chore_id: uuid.UUID
    request: UpdateChoreRequest


@dataclass
class DeleteChoreInput:
    """Input for DeleteChoreCommand.

    Attributes:
        user_id: Requesting user.
        chore_id: ID of the chore to delete.
    """

    user_id: uuid.UUID
    chore_id: uuid.UUID


def _chore_to_response(chore: Chore) -> ChoreResponse:
    """Convert a Chore domain entity to a ChoreResponse DTO."""
    return ChoreResponse(
        id=chore.id,
        name=chore.name,
        estimated_duration_minutes=chore.estimated_duration.value,
        category=chore.category,
        wheel_config=WheelConfigDTO(
            multiplicity=chore.wheel_config.multiplicity.value,
            time_weight_rules=[
                TimeWeightRuleDTO(hour=r.hour, weight=r.weight)
                for r in chore.wheel_config.time_weight_rules
            ],
        ),
        reward_value=chore.reward_value.value,
        created_at=chore.created_at,
        updated_at=chore.updated_at,
    )


class CreateChoreCommand(BaseCommand[CreateChoreInput, ChoreResponse]):
    """Creates a new chore for the authenticated user.

    Args:
        chore_repo: Chore repository for persistence.
    """

    def __init__(self, chore_repo: ChoreRepository) -> None:
        self._chore_repo = chore_repo

    async def execute(self, input_data: CreateChoreInput) -> ChoreResponse:
        """Create and persist a new chore.

        Args:
            input_data: Contains the user ID and creation request.

        Returns:
            ChoreResponse representing the created chore.
        """
        req = input_data.request

        time_rules = [
            TimeWeightRule(hour=r.hour, weight=r.weight) for r in req.time_weight_rules
        ]

        chore = Chore(
            user_id=input_data.user_id,
            name=req.name,
            estimated_duration=Duration(req.estimated_duration_minutes),
            category=req.category,
            wheel_config=WheelConfiguration(
                multiplicity=Multiplicity(req.multiplicity),
                time_weight_rules=time_rules,
            ),
            reward_value=RewardValue(req.reward_value),
        )

        chore = await self._chore_repo.add(chore)
        return _chore_to_response(chore)


class UpdateChoreCommand(BaseCommand[UpdateChoreInput, ChoreResponse]):
    """Updates an existing chore.

    Args:
        chore_repo: Chore repository for persistence.
    """

    def __init__(self, chore_repo: ChoreRepository) -> None:
        self._chore_repo = chore_repo

    async def execute(self, input_data: UpdateChoreInput) -> ChoreResponse:
        """Update an existing chore with the provided fields.

        Args:
            input_data: Contains the user ID, chore ID, and update request.

        Returns:
            ChoreResponse representing the updated chore.

        Raises:
            ChoreNotFoundError: If the chore does not exist.
            AuthorizationError: If the user does not own the chore.
        """
        chore = await self._chore_repo.get_by_id(input_data.chore_id)
        if chore is None:
            raise ChoreNotFoundError(str(input_data.chore_id))

        if chore.user_id != input_data.user_id:
            raise AuthorizationError("You do not own this chore")

        req = input_data.request

        if req.name is not None:
            chore.name = req.name
        if req.estimated_duration_minutes is not None:
            chore.estimated_duration = Duration(req.estimated_duration_minutes)
        if req.category is not None:
            chore.category = req.category
        if req.multiplicity is not None:
            chore.wheel_config.multiplicity = Multiplicity(req.multiplicity)
        if req.time_weight_rules is not None:
            chore.wheel_config.time_weight_rules = [
                TimeWeightRule(hour=r.hour, weight=r.weight) for r in req.time_weight_rules
            ]
        if req.reward_value is not None:
            chore.reward_value = RewardValue(req.reward_value)

        chore.updated_at = datetime.now(timezone.utc)
        chore = await self._chore_repo.update(chore)
        return _chore_to_response(chore)


class DeleteChoreCommand(BaseCommand[DeleteChoreInput, None]):
    """Deletes an existing chore.

    Args:
        chore_repo: Chore repository for persistence.
    """

    def __init__(self, chore_repo: ChoreRepository) -> None:
        self._chore_repo = chore_repo

    async def execute(self, input_data: DeleteChoreInput) -> None:
        """Delete a chore by its ID.

        Args:
            input_data: Contains the user ID and chore ID.

        Raises:
            ChoreNotFoundError: If the chore does not exist.
            AuthorizationError: If the user does not own the chore.
        """
        chore = await self._chore_repo.get_by_id(input_data.chore_id)
        if chore is None:
            raise ChoreNotFoundError(str(input_data.chore_id))

        if chore.user_id != input_data.user_id:
            raise AuthorizationError("You do not own this chore")

        await self._chore_repo.delete(input_data.chore_id)
