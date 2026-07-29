"""Smoke coverage for every API router."""

from httpx import ASGITransport, AsyncClient


async def test_health_router(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_tasks_router_list(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_backlog_router_list(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/backlog")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_routines_router_list(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/routines")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_appointments_router_list(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/appointments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_maintenance_router_list(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/maintenance")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_weekly_targets_router_list(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/weekly-targets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_settings_router_get(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/settings")
    assert response.status_code == 200
    assert "settings" in response.json()


async def test_views_router_today(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/views/today")
    assert response.status_code == 200
    assert "items" in response.json()
