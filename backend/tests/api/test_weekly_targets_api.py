"""API tests for weekly targets."""

from httpx import ASGITransport, AsyncClient


async def test_weekly_target_progress(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = (
            await client.post(
                "/api/weekly-targets",
                json={"title": "Demo walks", "target_count": 3},
            )
        ).json()
        await client.post(f"/api/weekly-targets/{created['id']}/progress")
        week = (await client.get("/api/views/week")).json()

    assert created["target_count"] == 3
    target_summary = next(
        target for target in week["targets"] if target["target_id"] == created["id"]
    )
    assert target_summary["completed_count"] == 1
