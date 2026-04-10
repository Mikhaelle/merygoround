"""SQLAlchemy implementation of the ChoreRepository."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from merygoround.domain.chores.entities import Chore, WheelConfiguration
from merygoround.domain.chores.repository import ChoreRepository
from merygoround.domain.chores.value_objects import Duration, Multiplicity, RewardValue, TimeWeightRule
from merygoround.infrastructure.database.models.chore import ChoreModel


class SqlAlchemyChoreRepository(ChoreRepository):
    """Concrete ChoreRepository backed by SQLAlchemy and PostgreSQL.

    Args:
        session: The async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, chore_id: uuid.UUID) -> Chore | None:
        """Retrieve a chore by its unique identifier.

        Args:
            chore_id: The UUID of the chore.

        Returns:
            The Chore domain entity if found, otherwise None.
        """
        model = await self._session.get(ChoreModel, chore_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[Chore]:
        """Retrieve all chores belonging to a user.

        Args:
            user_id: The UUID of the owning user.

        Returns:
            List of Chore domain entities.
        """
        stmt = select(ChoreModel).where(ChoreModel.user_id == user_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def add(self, chore: Chore) -> Chore:
        """Persist a new chore.

        Args:
            chore: The Chore domain entity to persist.

        Returns:
            The persisted Chore domain entity.
        """
        model = self._to_model(chore)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def update(self, chore: Chore) -> Chore:
        """Update an existing chore.

        Args:
            chore: The Chore domain entity with updated state.

        Returns:
            The updated Chore domain entity.
        """
        model = await self._session.get(ChoreModel, chore.id)
        if model is not None:
            model.name = chore.name
            model.estimated_duration_minutes = chore.estimated_duration.value
            model.category = chore.category
            model.multiplicity = chore.wheel_config.multiplicity.value
            model.time_weight_rules = [
                {"hour": r.hour, "weight": r.weight}
                for r in chore.wheel_config.time_weight_rules
            ]
            model.reward_value = chore.reward_value.value
            model.updated_at = chore.updated_at
            await self._session.flush()
        return chore

    async def delete(self, chore_id: uuid.UUID) -> None:
        """Remove a chore by its unique identifier.

        Args:
            chore_id: The UUID of the chore to remove.
        """
        stmt = delete(ChoreModel).where(ChoreModel.id == chore_id)
        await self._session.execute(stmt)
        await self._session.flush()

    def _to_domain(self, model: ChoreModel) -> Chore:
        """Map a ChoreModel ORM instance to a Chore domain entity."""
        time_rules = [
            TimeWeightRule(hour=r["hour"], weight=r["weight"])
            for r in (model.time_weight_rules or [])
        ]
        return Chore(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            estimated_duration=Duration(model.estimated_duration_minutes),
            category=model.category,
            wheel_config=WheelConfiguration(
                multiplicity=Multiplicity(model.multiplicity),
                time_weight_rules=time_rules,
            ),
            reward_value=RewardValue(Decimal(str(model.reward_value))),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, chore: Chore) -> ChoreModel:
        """Map a Chore domain entity to a ChoreModel ORM instance."""
        return ChoreModel(
            id=chore.id,
            user_id=chore.user_id,
            name=chore.name,
            estimated_duration_minutes=chore.estimated_duration.value,
            category=chore.category,
            multiplicity=chore.wheel_config.multiplicity.value,
            time_weight_rules=[
                {"hour": r.hour, "weight": r.weight}
                for r in chore.wheel_config.time_weight_rules
            ],
            reward_value=chore.reward_value.value,
            created_at=chore.created_at,
            updated_at=chore.updated_at,
        )
