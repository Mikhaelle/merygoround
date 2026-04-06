"""Wheel API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from merygoround.api.config import Settings
from merygoround.api.dependencies import get_current_user, get_session, get_settings
from merygoround.application.wheel.commands import (
    CompleteSpinInput,
    CompleteSpinSessionCommand,
    QuickCompleteChoreCommand,
    QuickCompleteChoreInput,
    QuickDeactivateChoreCommand,
    QuickDeactivateChoreInput,
    QuickSkipChoreCommand,
    QuickSkipChoreInput,
    ResetChoreCommand,
    ResetChoreInput,
    ResetDailyWheelCommand,
    ResetDailyWheelInput,
    SkipSpinInput,
    SkipSpinSessionCommand,
    SpinWheelCommand,
    SpinWheelInput,
)
from merygoround.application.wheel.dtos import (
    DailyProgressItem,
    SpinHistoryResponse,
    SpinResultResponse,
    WheelSegmentResponse,
)
from merygoround.application.wheel.queries import (
    GetDailyProgressQuery,
    GetSpinHistoryInput,
    GetSpinHistoryQuery,
    GetWheelSegmentsQuery,
)
from merygoround.domain.wheel.services import WheelSpinService
from merygoround.infrastructure.database.repositories.chore_repository import (
    SqlAlchemyChoreRepository,
)
from merygoround.infrastructure.database.repositories.spin_session_repository import (
    SqlAlchemySpinSessionRepository,
)

router = APIRouter(prefix="/wheel", tags=["wheel"])


@router.post("/spin", response_model=SpinResultResponse, status_code=201)
async def spin_wheel(
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SpinResultResponse:
    """Spin the wheel and get a random chore.

    Args:
        user_id: The authenticated user's UUID.
        session: Database session.
        settings: Application settings.

    Returns:
        SpinResultResponse with the selected chore.
    """
    tz = settings.APP_TIMEZONE
    chore_repo = SqlAlchemyChoreRepository(session)
    spin_repo = SqlAlchemySpinSessionRepository(session, tz_name=tz)
    spin_service = WheelSpinService()
    command = SpinWheelCommand(chore_repo, spin_repo, spin_service, tz_name=tz)
    return await command.execute(SpinWheelInput(user_id=user_id))


@router.put("/sessions/{session_id}/complete", status_code=204)
async def complete_session(
    session_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Mark a spin session as completed.

    Args:
        session_id: The UUID of the spin session.
        user_id: The authenticated user's UUID.
        session: Database session.
    """
    spin_repo = SqlAlchemySpinSessionRepository(session)
    command = CompleteSpinSessionCommand(spin_repo)
    await command.execute(CompleteSpinInput(user_id=user_id, session_id=session_id))


@router.put("/sessions/{session_id}/skip", status_code=204)
async def skip_session(
    session_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Mark a spin session as skipped.

    Args:
        session_id: The UUID of the spin session.
        user_id: The authenticated user's UUID.
        session: Database session.
    """
    spin_repo = SqlAlchemySpinSessionRepository(session)
    command = SkipSpinSessionCommand(spin_repo)
    await command.execute(SkipSpinInput(user_id=user_id, session_id=session_id))


@router.post("/chores/{chore_id}/complete", status_code=204)
async def quick_complete_chore(
    chore_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Mark one instance of a chore as completed for today.

    Args:
        chore_id: The UUID of the chore to complete.
        user_id: The authenticated user's UUID.
        session: Database session.
        settings: Application settings.
    """
    tz = settings.APP_TIMEZONE
    chore_repo = SqlAlchemyChoreRepository(session)
    spin_repo = SqlAlchemySpinSessionRepository(session, tz_name=tz)
    command = QuickCompleteChoreCommand(chore_repo, spin_repo, tz_name=tz)
    await command.execute(QuickCompleteChoreInput(user_id=user_id, chore_id=chore_id))


@router.post("/chores/{chore_id}/skip", status_code=204)
async def quick_skip_chore(
    chore_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Mark one instance of a chore as skipped for today.

    Args:
        chore_id: The UUID of the chore to skip.
        user_id: The authenticated user's UUID.
        session: Database session.
    """
    chore_repo = SqlAlchemyChoreRepository(session)
    spin_repo = SqlAlchemySpinSessionRepository(session)
    command = QuickSkipChoreCommand(chore_repo, spin_repo)
    await command.execute(QuickSkipChoreInput(user_id=user_id, chore_id=chore_id))


@router.post("/chores/{chore_id}/deactivate", status_code=204)
async def quick_deactivate_chore(
    chore_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Deactivate one instance of a chore for today (not needed today).

    Args:
        chore_id: The UUID of the chore to deactivate.
        user_id: The authenticated user's UUID.
        session: Database session.
        settings: Application settings.
    """
    tz = settings.APP_TIMEZONE
    chore_repo = SqlAlchemyChoreRepository(session)
    spin_repo = SqlAlchemySpinSessionRepository(session, tz_name=tz)
    command = QuickDeactivateChoreCommand(chore_repo, spin_repo, tz_name=tz)
    await command.execute(QuickDeactivateChoreInput(user_id=user_id, chore_id=chore_id))


@router.delete("/chores/{chore_id}/reset", status_code=204)
async def reset_chore(
    chore_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Reset a specific chore for today by deleting its spin sessions.

    Args:
        chore_id: The UUID of the chore to reset.
        user_id: The authenticated user's UUID.
        session: Database session.
        settings: Application settings.
    """
    tz = settings.APP_TIMEZONE
    spin_repo = SqlAlchemySpinSessionRepository(session, tz_name=tz)
    command = ResetChoreCommand(spin_repo, tz_name=tz)
    await command.execute(ResetChoreInput(user_id=user_id, chore_id=chore_id))


@router.get("/daily-progress", response_model=list[DailyProgressItem])
async def get_daily_progress(
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[DailyProgressItem]:
    """Get daily completion/skip/deactivation progress for all chores.

    Args:
        user_id: The authenticated user's UUID.
        session: Database session.
        settings: Application settings.

    Returns:
        List of DailyProgressItem DTOs.
    """
    tz = settings.APP_TIMEZONE
    chore_repo = SqlAlchemyChoreRepository(session)
    spin_repo = SqlAlchemySpinSessionRepository(session, tz_name=tz)
    query = GetDailyProgressQuery(chore_repo, spin_repo, tz_name=tz)
    return await query.execute(user_id)


@router.delete("/reset-daily", status_code=204)
async def reset_daily_wheel(
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Reset today's wheel by deleting all spin sessions for the current day.

    Args:
        user_id: The authenticated user's UUID.
        session: Database session.
        settings: Application settings.
    """
    tz = settings.APP_TIMEZONE
    spin_repo = SqlAlchemySpinSessionRepository(session, tz_name=tz)
    command = ResetDailyWheelCommand(spin_repo, tz_name=tz)
    await command.execute(ResetDailyWheelInput(user_id=user_id))


@router.get("/history", response_model=SpinHistoryResponse)
async def get_history(
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> SpinHistoryResponse:
    """Get paginated spin history.

    Args:
        user_id: The authenticated user's UUID.
        session: Database session.
        page: Page number (1-indexed).
        per_page: Number of items per page.

    Returns:
        SpinHistoryResponse with paginated spin sessions.
    """
    spin_repo = SqlAlchemySpinSessionRepository(session)
    query = GetSpinHistoryQuery(spin_repo)
    return await query.execute(
        GetSpinHistoryInput(user_id=user_id, page=page, per_page=per_page)
    )


@router.get("/segments", response_model=list[WheelSegmentResponse])
async def get_segments(
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[WheelSegmentResponse]:
    """Get wheel segments with effective weights for the current hour.

    Args:
        user_id: The authenticated user's UUID.
        session: Database session.
        settings: Application settings.

    Returns:
        List of WheelSegmentResponse DTOs.
    """
    tz = settings.APP_TIMEZONE
    chore_repo = SqlAlchemyChoreRepository(session)
    spin_repo = SqlAlchemySpinSessionRepository(session, tz_name=tz)
    spin_service = WheelSpinService()
    query = GetWheelSegmentsQuery(chore_repo, spin_repo, spin_service, tz_name=tz)
    return await query.execute(user_id)
