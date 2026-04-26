"""Aggregated v1 API router."""

from __future__ import annotations

from fastapi import APIRouter

from merygoround.api.v1.adult_bucket import router as adult_bucket_router
from merygoround.api.v1.auth import router as auth_router
from merygoround.api.v1.chores import router as chores_router
from merygoround.api.v1.dashboard import router as dashboard_router
from merygoround.api.v1.notifications import router as notifications_router
from merygoround.api.v1.wheel import router as wheel_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(chores_router)
v1_router.include_router(wheel_router)
v1_router.include_router(adult_bucket_router)
v1_router.include_router(notifications_router)
v1_router.include_router(dashboard_router)
