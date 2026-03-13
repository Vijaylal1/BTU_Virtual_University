"""Integration tests for FastAPI endpoints (uses httpx TestClient)."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from api.app import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "BTU" in data["service"]


@pytest.mark.asyncio
async def test_chat_requires_auth(client: AsyncClient):
    response = await client.post("/chat", json={"message": "hello"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    """Smoke test: register a new student and login."""
    # This test requires a real DB; skip if unavailable
    pytest.skip("Requires live PostgreSQL – run with docker compose")
