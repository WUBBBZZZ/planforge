"""API tests for routines."""

from httpx import ASGITransport, AsyncClient


async def test_create_and_pause_routine(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = (
            await client.post(
                "/api/routines",
                json={
                    "title": "Demo laundry",
                    "schedule_type": "weekly",
                    "days_of_week": [6],
                    "interval_weeks": 1,
                },
            )
        ).json()
        paused = (await client.post(f"/api/routines/{created['id']}/pause")).json()

    assert created["status"] == "active"
    assert paused["status"] == "paused"


async def test_sync_occurrences_returns_204(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/routines",
            json={
                "title": "Demo dishes",
                "schedule_type": "weekly",
                "days_of_week": [0],
            },
        )
        response = await client.post("/api/routines/sync-occurrences")

    assert response.status_code == 204
