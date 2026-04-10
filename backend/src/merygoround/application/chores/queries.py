"""Query use cases for the Chores bounded context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from merygoround.application.chores.dtos import (
    ChoreResponse,
    TimeWeightRuleDTO,
    WheelConfigDTO,
)
from merygoround.application.shared.use_case import BaseQuery
from merygoround.domain.chores.entities import Chore
from merygoround.domain.chores.exceptions import ChoreNotFoundError
from merygoround.domain.shared.exceptions import AuthorizationError

if TYPE_CHECKING:
    from merygoround.domain.chores.repository import ChoreRepository


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


class ListChoresQuery(BaseQuery[uuid.UUID, list[ChoreResponse]]):
    """Retrieves all chores for the authenticated user.

    Args:
        chore_repo: Chore repository for lookup.
    """

    def __init__(self, chore_repo: ChoreRepository) -> None:
        self._chore_repo = chore_repo

    async def execute(self, input_data: uuid.UUID) -> list[ChoreResponse]:
        """List all chores belonging to the user.

        Args:
            input_data: The UUID of the authenticated user.

        Returns:
            List of ChoreResponse DTOs.
        """
        chores = await self._chore_repo.get_by_user_id(input_data)
        return [_chore_to_response(c) for c in chores]


@dataclass
class GetChoreInput:
    """Input for GetChoreQuery.

    Attributes:
        user_id: Requesting user.
        chore_id: ID of the chore to retrieve.
    """

    user_id: uuid.UUID
    chore_id: uuid.UUID


class GetChoreQuery(BaseQuery[GetChoreInput, ChoreResponse]):
    """Retrieves a single chore by its ID.

    Args:
        chore_repo: Chore repository for lookup.
    """

    def __init__(self, chore_repo: ChoreRepository) -> None:
        self._chore_repo = chore_repo

    async def execute(self, input_data: GetChoreInput) -> ChoreResponse:
        """Retrieve a chore by its ID.

        Args:
            input_data: Contains the user ID and chore ID.

        Returns:
            ChoreResponse for the requested chore.

        Raises:
            ChoreNotFoundError: If the chore does not exist.
            AuthorizationError: If the user does not own the chore.
        """
        chore = await self._chore_repo.get_by_id(input_data.chore_id)
        if chore is None:
            raise ChoreNotFoundError(str(input_data.chore_id))

        if chore.user_id != input_data.user_id:
            raise AuthorizationError("You do not own this chore")

        return _chore_to_response(chore)
