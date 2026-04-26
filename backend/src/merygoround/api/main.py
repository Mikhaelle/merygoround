"""FastAPI application factory and lifespan management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from merygoround.api.config import Settings
from merygoround.api.middleware import register_exception_handlers
from merygoround.api.v1.router import v1_router
from merygoround.infrastructure.database.engine import create_async_engine, create_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Initializes the database engine, session factory, and notification
    scheduler on startup. Shuts down the scheduler and disposes the
    engine on shutdown.
    """
    settings = Settings()

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = create_session_factory(engine)

    app.state.engine = engine
    app.state.session_factory = session_factory

    scheduler = None
    if settings.VAPID_PRIVATE_KEY:
        try:
            from merygoround.infrastructure.push.web_push_service import (
                PyWebPushNotificationService,
            )
            from merygoround.infrastructure.scheduler.notification_scheduler import (
                NotificationScheduler,
            )

            push_service = PyWebPushNotificationService(
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_CLAIMS_EMAIL},
            )
            scheduler = NotificationScheduler(
                session_factory=session_factory,
                push_service=push_service,
                tz_name=settings.APP_TIMEZONE,
            )
            scheduler.start()
        except Exception:
            logger.exception("Failed to start notification scheduler")

    yield

    if scheduler is not None:
        scheduler.shutdown()

    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured FastAPI application instance.
    """
    settings = Settings()

    app = FastAPI(
        title="MeryGoRound API",
        description="Household chore spinning wheel with adult life task bucket",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()
