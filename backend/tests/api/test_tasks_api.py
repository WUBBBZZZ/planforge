"""API tests for tasks and views."""

from httpx import ASGITransport, AsyncClient


async def test_create_task_returns_201(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/tasks",
            json={"title": "Water the plants", "due_date": "2026-07-21"},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Water the plants"
    assert payload["status"] == "pending"


async def test_create_task_empty_title_returns_422(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/tasks", json={"title": "   "})

    assert response.status_code == 422


async def test_today_view_structure(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/tasks",
            json={"title": "Today demo", "due_date": "2026-07-21"},
        )
        response = await client.get("/api/views/today", params={"date": "2026-07-21"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["reference_date"] == "2026-07-21"
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "Today demo"


async def test_complete_stays_on_today_as_completed(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        today_response = await client.get("/api/views/today")
        reference_date = today_response.json()["reference_date"]
        create_response = await client.post(
            "/api/tasks",
            json={"title": "Finish demo", "due_date": reference_date},
        )
        task_id = create_response.json()["id"]
        await client.post(f"/api/tasks/{task_id}/complete")
        today_response = await client.get(
            "/api/views/today",
            params={"date": reference_date},
        )

    payload = today_response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["is_completed"] is True
