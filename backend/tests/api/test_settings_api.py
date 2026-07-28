"""API tests for settings endpoints."""

from httpx import ASGITransport, AsyncClient


async def test_update_timezone_setting(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/api/settings/timezone",
            json={"value": "America/Los_Angeles"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["settings"]["timezone"] == "America/Los_Angeles"


async def test_update_timezone_invalid_value_returns_422(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/api/settings/timezone",
            json={"value": "Not/A_Real_Zone"},
        )

    assert response.status_code == 422


async def test_update_timezone_utc_alias(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/api/settings/timezone",
            json={"value": "UTC"},
        )

    assert response.status_code == 200
    assert response.json()["settings"]["timezone"] == "UTC"
