"""Tests for the health endpoint."""

from httpx import ASGITransport, AsyncClient
from planforge.main import create_app


async def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
