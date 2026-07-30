"""API tests for backlog."""

from httpx import ASGITransport, AsyncClient


async def test_backlog_create_and_archive(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = (
            await client.post(
                "/api/backlog",
                json={"title": "Someday demo idea", "notes": "Fabricated only"},
            )
        ).json()
        archived = (await client.post(f"/api/backlog/{created['id']}/archive")).json()

    assert created["status"] == "active"
    assert archived["status"] == "archived"


async def test_backlog_delete(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = (
            await client.post(
                "/api/backlog",
                json={"title": "Delete me"},
            )
        ).json()
        delete_response = await client.delete(f"/api/backlog/{created['id']}")
        list_response = await client.get("/api/backlog")

    assert delete_response.status_code == 204
    assert list_response.json() == []


async def test_backlog_promote_to_task(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = (
            await client.post("/api/backlog", json={"title": "Promote demo task"})
        ).json()
        promoted = (
            await client.post(
                f"/api/backlog/{created['id']}/promote",
                json={"due_date": "2026-07-21"},
            )
        ).json()

    assert promoted["task"]["title"] == "Promote demo task"
    assert promoted["backlog"]["status"] == "promoted"
