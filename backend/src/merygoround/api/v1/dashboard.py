"""Dashboard API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from merygoround.api.config import Settings
from merygoround.api.dependencies import get_current_user, get_session, get_settings
from merygoround.application.dashboard.dtos import DashboardResponse, PeriodLiteral
from merygoround.application.dashboard.queries import GetDashboardInput, GetDashboardQuery

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    user_id: Annotated[uuid.UUID, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    period: Annotated[PeriodLiteral, Query(description="7d, 30d, 90d or year")] = "7d",
) -> DashboardResponse:
    """Return the aggregated dashboard payload for the authenticated user."""
    query = GetDashboardQuery(session)
    return await query.execute(
        GetDashboardInput(
            user_id=user_id,
            period=period,
            tz_name=settings.APP_TIMEZONE,
        )
    )
