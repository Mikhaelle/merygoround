"""End-to-end tests for the Wheel API endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from merygoround.infrastructure.auth.jwt_service import JWTService
from merygoround.infrastructure.database.models.chore import ChoreModel
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
    return uuid.UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def auth_headers(jwt_service: JWTService, user_id: uuid.UUID) -> dict[str, str]:
    """Provide authorization headers with a valid access token."""
    token = jwt_service.create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seed_user(session, user_id: uuid.UUID) -> None:
    """Insert a test user into the database."""
    user = UserModel(
        id=user_id,
        email="wheel-test@example.com",
        name="Wheel Tester",
        hashed_password="fakehash",
    )
    session.add(user)
    await session.flush()


@pytest.fixture
async def seed_chores(session, user_id: uuid.UUID, seed_user) -> list[uuid.UUID]:
    """Insert test chores and return their IDs."""
    chore_ids = []
    for i, (name, mult) in enumerate([("Dishes", 1), ("Laundry", 2), ("Vacuum", 1)]):
        cid = uuid.uuid4()
        chore = ChoreModel(
            id=cid,
            user_id=user_id,
            name=name,
            estimated_duration_minutes=5,
            category="Cleaning",
            multiplicity=mult,
        )
        session.add(chore)
        chore_ids.append(cid)
    await session.flush()
    return chore_ids


class TestSpinEndpoint:
    """Test suite for POST /api/v1/wheel/spin."""

    async def test_spin_returns_201_with_pending_session(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Spinning creates a PENDING session and returns 201."""
        resp = await client.post("/api/v1/wheel/spin", headers=auth_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "PENDING"
        assert "id" in data
        assert "chore" in data

    async def test_spin_requires_auth(self, client: AsyncClient, seed_chores) -> None:
        """Spinning without auth returns 401."""
        resp = await client.post("/api/v1/wheel/spin")
        assert resp.status_code == 401


class TestCompleteEndpoint:
    """Test suite for PUT /api/v1/wheel/sessions/{id}/complete."""

    async def test_complete_returns_204(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Completing a spin session returns 204."""
        spin_resp = await client.post("/api/v1/wheel/spin", headers=auth_headers)
        session_id = spin_resp.json()["id"]

        resp = await client.put(
            f"/api/v1/wheel/sessions/{session_id}/complete", headers=auth_headers
        )
        assert resp.status_code == 204

    async def test_complete_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Completing a nonexistent session returns 404."""
        fake_id = uuid.uuid4()
        resp = await client.put(
            f"/api/v1/wheel/sessions/{fake_id}/complete", headers=auth_headers
        )
        assert resp.status_code == 404


class TestSkipEndpoint:
    """Test suite for PUT /api/v1/wheel/sessions/{id}/skip."""

    async def test_skip_returns_204(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Skipping a spin session returns 204."""
        spin_resp = await client.post("/api/v1/wheel/spin", headers=auth_headers)
        session_id = spin_resp.json()["id"]

        resp = await client.put(
            f"/api/v1/wheel/sessions/{session_id}/skip", headers=auth_headers
        )
        assert resp.status_code == 204


class TestSegmentsEndpoint:
    """Test suite for GET /api/v1/wheel/segments."""

    async def test_segments_returns_all_chores(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Segments include all chores when none are completed."""
        resp = await client.get("/api/v1/wheel/segments", headers=auth_headers)

        assert resp.status_code == 200
        segments = resp.json()
        assert len(segments) == 3

    async def test_segments_excludes_completed_chore(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Completed chores with multiplicity=1 are excluded from segments."""
        chore_id = str(seed_chores[0])  # Dishes, multiplicity=1
        await client.post(
            f"/api/v1/wheel/chores/{chore_id}/complete", headers=auth_headers
        )

        resp = await client.get("/api/v1/wheel/segments", headers=auth_headers)
        segment_ids = [s["chore_id"] for s in resp.json()]
        assert chore_id not in segment_ids

    async def test_segments_excludes_skipped_chore(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Skipped chores with multiplicity=1 are excluded from segments."""
        spin_resp = await client.post("/api/v1/wheel/spin", headers=auth_headers)
        session_id = spin_resp.json()["id"]
        skipped_chore_id = spin_resp.json()["chore"]["id"]

        await client.put(
            f"/api/v1/wheel/sessions/{session_id}/skip", headers=auth_headers
        )

        resp = await client.get("/api/v1/wheel/segments", headers=auth_headers)
        segments = resp.json()
        segment_ids = [s["chore_id"] for s in segments]
        assert skipped_chore_id not in segment_ids


class TestQuickCompleteEndpoint:
    """Test suite for POST /api/v1/wheel/chores/{id}/complete."""

    async def test_quick_complete_returns_204(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Quick completing a chore returns 204."""
        resp = await client.post(
            f"/api/v1/wheel/chores/{seed_chores[0]}/complete", headers=auth_headers
        )
        assert resp.status_code == 204

    async def test_quick_complete_removes_from_segments(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Quick completed chore disappears from wheel segments."""
        chore_id = str(seed_chores[0])
        await client.post(
            f"/api/v1/wheel/chores/{chore_id}/complete", headers=auth_headers
        )

        resp = await client.get("/api/v1/wheel/segments", headers=auth_headers)
        segment_ids = [s["chore_id"] for s in resp.json()]
        assert chore_id not in segment_ids

    async def test_quick_complete_nonexistent_chore_returns_404(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Quick completing a nonexistent chore returns 404."""
        resp = await client.post(
            f"/api/v1/wheel/chores/{uuid.uuid4()}/complete", headers=auth_headers
        )
        assert resp.status_code == 404


class TestQuickSkipEndpoint:
    """Test suite for POST /api/v1/wheel/chores/{id}/skip."""

    async def test_quick_skip_returns_204(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Quick skipping a chore returns 204."""
        resp = await client.post(
            f"/api/v1/wheel/chores/{seed_chores[0]}/skip", headers=auth_headers
        )
        assert resp.status_code == 204

    async def test_quick_skip_removes_from_segments(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Quick skipped chore disappears from wheel segments."""
        chore_id = str(seed_chores[0])
        await client.post(
            f"/api/v1/wheel/chores/{chore_id}/skip", headers=auth_headers
        )

        resp = await client.get("/api/v1/wheel/segments", headers=auth_headers)
        segment_ids = [s["chore_id"] for s in resp.json()]
        assert chore_id not in segment_ids


class TestDailyProgressEndpoint:
    """Test suite for GET /api/v1/wheel/daily-progress."""

    async def test_returns_progress_for_all_chores(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Daily progress includes an entry for every chore."""
        resp = await client.get("/api/v1/wheel/daily-progress", headers=auth_headers)

        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 3

    async def test_progress_reflects_completions(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Progress reflects quick completions and skips."""
        await client.post(
            f"/api/v1/wheel/chores/{seed_chores[0]}/complete", headers=auth_headers
        )
        await client.post(
            f"/api/v1/wheel/chores/{seed_chores[1]}/skip", headers=auth_headers
        )

        resp = await client.get("/api/v1/wheel/daily-progress", headers=auth_headers)
        items = {item["chore_id"]: item for item in resp.json()}

        assert items[str(seed_chores[0])]["completed"] == 1
        assert items[str(seed_chores[1])]["skipped"] == 1
        assert items[str(seed_chores[2])]["completed"] == 0


class TestResetChoreEndpoint:
    """Test suite for DELETE /api/v1/wheel/chores/{id}/reset."""

    async def test_reset_chore_returns_204(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Resetting a chore returns 204."""
        await client.post(
            f"/api/v1/wheel/chores/{seed_chores[0]}/complete", headers=auth_headers
        )

        resp = await client.delete(
            f"/api/v1/wheel/chores/{seed_chores[0]}/reset", headers=auth_headers
        )
        assert resp.status_code == 204

    async def test_reset_chore_restores_to_wheel(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Resetting a completed chore puts it back on the wheel."""
        chore_id = str(seed_chores[0])
        await client.post(
            f"/api/v1/wheel/chores/{chore_id}/complete", headers=auth_headers
        )

        segs_before = await client.get("/api/v1/wheel/segments", headers=auth_headers)
        assert chore_id not in [s["chore_id"] for s in segs_before.json()]

        await client.delete(
            f"/api/v1/wheel/chores/{chore_id}/reset", headers=auth_headers
        )

        segs_after = await client.get("/api/v1/wheel/segments", headers=auth_headers)
        assert chore_id in [s["chore_id"] for s in segs_after.json()]

    async def test_reset_chore_only_affects_target(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Resetting one chore does not affect other chores' progress."""
        await client.post(
            f"/api/v1/wheel/chores/{seed_chores[0]}/complete", headers=auth_headers
        )
        await client.post(
            f"/api/v1/wheel/chores/{seed_chores[2]}/complete", headers=auth_headers
        )

        await client.delete(
            f"/api/v1/wheel/chores/{seed_chores[0]}/reset", headers=auth_headers
        )

        resp = await client.get("/api/v1/wheel/daily-progress", headers=auth_headers)
        items = {item["chore_id"]: item for item in resp.json()}
        assert items[str(seed_chores[0])]["completed"] == 0
        assert items[str(seed_chores[2])]["completed"] == 1


class TestResetDailyEndpoint:
    """Test suite for DELETE /api/v1/wheel/reset-daily."""

    async def test_reset_daily_returns_204(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Resetting the full day returns 204."""
        await client.post(
            f"/api/v1/wheel/chores/{seed_chores[0]}/complete", headers=auth_headers
        )

        resp = await client.delete("/api/v1/wheel/reset-daily", headers=auth_headers)
        assert resp.status_code == 204

    async def test_reset_daily_restores_all_to_wheel(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Resetting the day puts all chores back on the wheel."""
        for cid in seed_chores:
            await client.post(
                f"/api/v1/wheel/chores/{cid}/complete", headers=auth_headers
            )

        await client.delete("/api/v1/wheel/reset-daily", headers=auth_headers)

        resp = await client.get("/api/v1/wheel/segments", headers=auth_headers)
        assert len(resp.json()) == 3

    async def test_reset_daily_zeros_progress(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """After daily reset, all progress counters are zero."""
        await client.post(
            f"/api/v1/wheel/chores/{seed_chores[0]}/complete", headers=auth_headers
        )
        await client.post(
            f"/api/v1/wheel/chores/{seed_chores[1]}/skip", headers=auth_headers
        )

        await client.delete("/api/v1/wheel/reset-daily", headers=auth_headers)

        resp = await client.get("/api/v1/wheel/daily-progress", headers=auth_headers)
        for item in resp.json():
            assert item["completed"] == 0
            assert item["skipped"] == 0


class TestHistoryEndpoint:
    """Test suite for GET /api/v1/wheel/history."""

    async def test_history_returns_paginated_results(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """History returns paginated spin sessions."""
        await client.post("/api/v1/wheel/spin", headers=auth_headers)
        await client.post("/api/v1/wheel/spin", headers=auth_headers)

        resp = await client.get("/api/v1/wheel/history", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert "items" in data

    async def test_history_includes_completed_status(
        self, client: AsyncClient, auth_headers, seed_chores
    ) -> None:
        """Completed sessions appear in history with COMPLETED status."""
        spin_resp = await client.post("/api/v1/wheel/spin", headers=auth_headers)
        session_id = spin_resp.json()["id"]

        await client.put(
            f"/api/v1/wheel/sessions/{session_id}/complete", headers=auth_headers
        )

        resp = await client.get("/api/v1/wheel/history", headers=auth_headers)
        items = resp.json()["items"]
        statuses = {item["id"]: item["status"] for item in items}
        assert statuses[session_id] == "COMPLETED"
