"""Global exception handling middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from merygoround.domain.adult_bucket.exceptions import (
    BucketItemNotFoundError,
    InvalidMaxInProgressError,
    MaxInProgressReachedError,
    NoBucketItemsError,
)
from merygoround.domain.chores.exceptions import ChoreNotFoundError
from merygoround.domain.identity.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from merygoround.domain.notification.exceptions import SubscriptionNotFoundError
from merygoround.domain.shared.exceptions import (
    AuthorizationError,
    DomainException,
    EntityNotFoundError,
    ValidationError,
)
from merygoround.domain.wheel.exceptions import NoChoresAvailableError

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

_NOT_FOUND_EXCEPTIONS = (
    EntityNotFoundError,
    UserNotFoundError,
    ChoreNotFoundError,
    BucketItemNotFoundError,
    SubscriptionNotFoundError,
)

_CONFLICT_EXCEPTIONS = (
    DuplicateEmailError,
    MaxInProgressReachedError,
)

_BAD_REQUEST_EXCEPTIONS = (
    ValidationError,
    NoBucketItemsError,
    NoChoresAvailableError,
    InvalidMaxInProgressError,
)

_UNAUTHORIZED_EXCEPTIONS = (
    InvalidCredentialsError,
)

_FORBIDDEN_EXCEPTIONS = (
    AuthorizationError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers that map domain exceptions to HTTP responses.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(DomainException)
    async def domain_exception_handler(
        request: Request, exc: DomainException
    ) -> JSONResponse:
        """Map domain exceptions to appropriate HTTP status codes."""
        if isinstance(exc, _NOT_FOUND_EXCEPTIONS):
            return JSONResponse(
                status_code=404,
                content={"detail": exc.message},
            )

        if isinstance(exc, _CONFLICT_EXCEPTIONS):
            return JSONResponse(
                status_code=409,
                content={"detail": exc.message},
            )

        if isinstance(exc, _BAD_REQUEST_EXCEPTIONS):
            return JSONResponse(
                status_code=400,
                content={"detail": exc.message},
            )

        if isinstance(exc, _UNAUTHORIZED_EXCEPTIONS):
            return JSONResponse(
                status_code=401,
                content={"detail": exc.message},
            )

        if isinstance(exc, _FORBIDDEN_EXCEPTIONS):
            return JSONResponse(
                status_code=403,
                content={"detail": exc.message},
            )

        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred"},
        )
