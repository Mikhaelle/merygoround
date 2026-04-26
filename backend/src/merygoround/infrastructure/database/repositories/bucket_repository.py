"""SQLAlchemy implementations of the Adult Bucket repositories."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select

from merygoround.domain.adult_bucket.entities import (
    BucketItem,
    BucketKind,
    BucketSettings,
    KanbanStatus,
)
from merygoround.domain.adult_bucket.repository import (
    BucketItemRepository,
    BucketSettingsRepository,
)
from merygoround.infrastructure.database.models.bucket import (
    BucketItemModel,
    BucketSettingsModel,
)

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyBucketItemRepository(BucketItemRepository):
    """Concrete BucketItemRepository backed by SQLAlchemy and PostgreSQL.

    Args:
        session: The async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: uuid.UUID) -> BucketItem | None:
        """Retrieve a bucket item by its unique identifier (no kind filter)."""
        model = await self._session.get(BucketItemModel, item_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def get_by_user_and_kind(
        self, user_id: uuid.UUID, kind: BucketKind
    ) -> list[BucketItem]:
        """Retrieve all bucket items for a user/kind, ordered for board display."""
        stmt = (
            select(BucketItemModel)
            .where(
                BucketItemModel.user_id == user_id,
                BucketItemModel.kind == kind.value,
            )
            .order_by(BucketItemModel.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_in_progress(self, user_id: uuid.UUID, kind: BucketKind) -> int:
        """Count IN_PROGRESS items for a user/kind."""
        stmt = (
            select(func.count())
            .select_from(BucketItemModel)
            .where(
                BucketItemModel.user_id == user_id,
                BucketItemModel.kind == kind.value,
                BucketItemModel.status == KanbanStatus.IN_PROGRESS.value,
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_to_do_for_user_and_kind(
        self, user_id: uuid.UUID, kind: BucketKind
    ) -> list[BucketItem]:
        """Retrieve all TO_DO items for a user/kind."""
        stmt = select(BucketItemModel).where(
            BucketItemModel.user_id == user_id,
            BucketItemModel.kind == kind.value,
            BucketItemModel.status == KanbanStatus.TO_DO.value,
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def add(self, item: BucketItem) -> BucketItem:
        """Persist a new bucket item."""
        model = BucketItemModel(
            id=item.id,
            user_id=item.user_id,
            name=item.name,
            description=item.description,
            category=item.category,
            status=item.status.value,
            kind=item.kind.value,
            started_at=item.started_at,
            completed_at=item.completed_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def update(self, item: BucketItem) -> BucketItem:
        """Update an existing bucket item."""
        model = await self._session.get(BucketItemModel, item.id)
        if model is not None:
            model.name = item.name
            model.description = item.description
            model.category = item.category
            model.status = item.status.value
            model.kind = item.kind.value
            model.started_at = item.started_at
            model.completed_at = item.completed_at
            model.updated_at = item.updated_at
            await self._session.flush()
        return item

    async def delete(self, item_id: uuid.UUID) -> None:
        """Remove a bucket item by its unique identifier."""
        stmt = delete(BucketItemModel).where(BucketItemModel.id == item_id)
        await self._session.execute(stmt)
        await self._session.flush()

    def _to_domain(self, model: BucketItemModel) -> BucketItem:
        """Map a BucketItemModel ORM instance to a BucketItem domain entity."""
        return BucketItem(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            category=model.category,
            status=KanbanStatus(model.status),
            kind=BucketKind(model.kind),
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyBucketSettingsRepository(BucketSettingsRepository):
    """Concrete BucketSettingsRepository backed by SQLAlchemy and PostgreSQL.

    Args:
        session: The async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_and_kind(
        self, user_id: uuid.UUID, kind: BucketKind
    ) -> BucketSettings | None:
        """Retrieve the settings for a user/kind, if persisted."""
        stmt = select(BucketSettingsModel).where(
            BucketSettingsModel.user_id == user_id,
            BucketSettingsModel.kind == kind.value,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def upsert(self, settings: BucketSettings) -> BucketSettings:
        """Insert or update the settings for the user/kind tuple."""
        stmt = select(BucketSettingsModel).where(
            BucketSettingsModel.user_id == settings.user_id,
            BucketSettingsModel.kind == settings.kind.value,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = BucketSettingsModel(
                id=settings.id,
                user_id=settings.user_id,
                kind=settings.kind.value,
                max_in_progress=settings.max_in_progress,
                created_at=settings.created_at,
                updated_at=settings.updated_at,
            )
            self._session.add(model)
        else:
            model.max_in_progress = settings.max_in_progress
            model.updated_at = settings.updated_at

        await self._session.flush()
        return self._to_domain(model)

    def _to_domain(self, model: BucketSettingsModel) -> BucketSettings:
        """Map a BucketSettingsModel ORM instance to a BucketSettings entity."""
        return BucketSettings(
            id=model.id,
            user_id=model.user_id,
            kind=BucketKind(model.kind),
            max_in_progress=model.max_in_progress,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
