"""End-to-end tests for the Adult Bucket Kanban API endpoints."""

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
        email="bucket-test@example.com",
        name="Bucket Tester",
        hashed_password="fakehash",
    )
    session.add(user)
    await session.flush()


async def _create_item(client: AsyncClient, headers: dict[str, str], name: str) -> dict:
    """Create an item and return the JSON payload."""
    resp = await client.post(
        "/api/v1/bucket/adult/items",
        json={"name": name, "description": "x", "category": "general"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestBucketKanbanApi:
    """End-to-end tests for the Bucket Kanban routes."""

    async def test_create_item_lands_in_to_do(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """A newly created item starts in TO_DO."""
        item = await _create_item(client, auth_headers, "Renew passport")
        assert item["status"] == "to_do"
        assert item["started_at"] is None
        assert item["completed_at"] is None

    async def test_default_settings_returns_two(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """GET /settings returns the default max_in_progress when none is persisted."""
        resp = await client.get("/api/v1/bucket/adult/settings", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == {"max_in_progress": 2}

    async def test_update_settings_persists_value(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """PUT /settings persists the new max_in_progress value."""
        resp = await client.put(
            "/api/v1/bucket/adult/settings",
            json={"max_in_progress": 4},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == {"max_in_progress": 4}

        get_resp = await client.get("/api/v1/bucket/adult/settings", headers=auth_headers)
        assert get_resp.json() == {"max_in_progress": 4}

    async def test_move_to_in_progress_under_limit(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """Moving the first item into IN_PROGRESS succeeds."""
        item = await _create_item(client, auth_headers, "Pay taxes")
        resp = await client.put(
            f"/api/v1/bucket/adult/items/{item['id']}/move",
            json={"status": "in_progress"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "in_progress"
        assert body["started_at"] is not None

    async def test_move_to_in_progress_blocked_at_max(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """Moving a third item into IN_PROGRESS at the default max=2 returns 409."""
        items = [
            await _create_item(client, auth_headers, f"Task {i}") for i in range(3)
        ]
        for item in items[:2]:
            resp = await client.put(
                f"/api/v1/bucket/adult/items/{item['id']}/move",
                json={"status": "in_progress"},
                headers=auth_headers,
            )
            assert resp.status_code == 200

        resp = await client.put(
            f"/api/v1/bucket/adult/items/{items[2]['id']}/move",
            json={"status": "in_progress"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_move_to_done_then_reopen(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """An item can be moved into DONE and back to IN_PROGRESS."""
        item = await _create_item(client, auth_headers, "Annual checkup")
        resp = await client.put(
            f"/api/v1/bucket/adult/items/{item['id']}/move",
            json={"status": "done"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["completed_at"] is not None

        resp = await client.put(
            f"/api/v1/bucket/adult/items/{item['id']}/move",
            json={"status": "in_progress"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    async def test_draw_returns_random_to_do_item(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """POST /draw suggests a random TO_DO item without changing its state."""
        item = await _create_item(client, auth_headers, "Buy groceries")
        resp = await client.post("/api/v1/bucket/adult/draw", headers=auth_headers)
        assert resp.status_code == 200
        suggestion = resp.json()["item"]
        assert suggestion["id"] == item["id"]
        assert suggestion["status"] == "to_do"

    async def test_draw_blocked_when_in_progress_at_max(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """POST /draw returns 409 when IN_PROGRESS is already at max."""
        items = [
            await _create_item(client, auth_headers, f"Task {i}") for i in range(3)
        ]
        for item in items[:2]:
            await client.put(
                f"/api/v1/bucket/adult/items/{item['id']}/move",
                json={"status": "in_progress"},
                headers=auth_headers,
            )

        resp = await client.post("/api/v1/bucket/adult/draw", headers=auth_headers)
        assert resp.status_code == 409

    async def test_draw_returns_400_when_no_to_do_items(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """POST /draw returns 400 when TO_DO is empty (and max is not yet reached)."""
        resp = await client.post("/api/v1/bucket/adult/draw", headers=auth_headers)
        assert resp.status_code == 400

    async def test_settings_rejects_zero(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """PUT /settings with max_in_progress=0 is rejected by the schema."""
        resp = await client.put(
            "/api/v1/bucket/adult/settings",
            json={"max_in_progress": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_adult_and_happy_boards_are_isolated(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """Items and settings of one board do not leak into the other."""
        adult_item = await _create_item(client, auth_headers, "Adult thing")
        happy_resp = await client.post(
            "/api/v1/bucket/happy/items",
            json={"name": "Happy thing", "description": "y"},
            headers=auth_headers,
        )
        assert happy_resp.status_code == 201
        happy_item = happy_resp.json()
        assert happy_item["kind"] == "happy"
        assert adult_item["kind"] == "adult"

        adult_list = (await client.get("/api/v1/bucket/adult/items", headers=auth_headers)).json()
        happy_list = (await client.get("/api/v1/bucket/happy/items", headers=auth_headers)).json()
        adult_names = {i["name"] for i in adult_list}
        happy_names = {i["name"] for i in happy_list}
        assert adult_names == {"Adult thing"}
        assert happy_names == {"Happy thing"}

        await client.put(
            "/api/v1/bucket/happy/settings",
            json={"max_in_progress": 5},
            headers=auth_headers,
        )
        adult_settings = (
            await client.get("/api/v1/bucket/adult/settings", headers=auth_headers)
        ).json()
        happy_settings = (
            await client.get("/api/v1/bucket/happy/settings", headers=auth_headers)
        ).json()
        assert adult_settings == {"max_in_progress": 2}
        assert happy_settings == {"max_in_progress": 5}

    async def test_cross_kind_move_returns_404(
        self, client: AsyncClient, seed_user, auth_headers: dict[str, str]
    ) -> None:
        """Trying to move an adult item via the happy route returns 404."""
        item = await _create_item(client, auth_headers, "Adult only")
        resp = await client.put(
            f"/api/v1/bucket/happy/items/{item['id']}/move",
            json={"status": "in_progress"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
