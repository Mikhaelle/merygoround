"""End-to-end tests for the Dashboard API.

The dashboard SQL aggregations rely on PostgreSQL-specific features
(``AT TIME ZONE``, ``date_trunc``, ``EXTRACT(ISODOW)``, etc.) that the
SQLite-backed test fixtures cannot execute. Aggregation behaviour is
validated against a real Postgres in development; here we focus on the
contract: routing, auth and request-level validation.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from merygoround.infrastructure.auth.jwt_service import JWTService
from merygoround.infrastructure.database.models.user import UserModel


@pytest.fixture
def jwt_service() -> JWTService:
    """Provide a JWTService configured for testing."""
    return JWTService(
        secret_key="test-secret-key-for-testing-only",
        algorithm="HS256",
    )


@pytest.fixture
def user_id() -> uuid.UUID:
    """Provide a fixed user UUID."""
    return uuid.UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture
def auth_headers(jwt_service: JWTService, user_id: uuid.UUID) -> dict[str, str]:
    """Provide authorization headers with a valid access token."""
    token = jwt_service.create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seed_user(session, user_id: uuid.UUID) -> None:
    """Insert a test user."""
    user = UserModel(
        id=user_id,
        email="dash-test@example.com",
        name="Dashboard Tester",
        hashed_password="fakehash",
    )
    session.add(user)
    await session.flush()


class TestDashboardApi:
    """Routing/auth/validation contract for GET /api/v1/dashboard."""

    async def test_unauthenticated_is_rejected(self, client: AsyncClient) -> None:
        """Missing the Authorization header returns 401/403."""
        resp = await client.get("/api/v1/dashboard")
        assert resp.status_code in {401, 403}

    async def test_invalid_period_returns_422(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """An unsupported period value is rejected by FastAPI validation."""
        resp = await client.get(
            "/api/v1/dashboard?period=invalid", headers=auth_headers
        )
        assert resp.status_code == 422

