"""Tests ensuring planner view GET endpoints do not persist side effects."""

from httpx import ASGITransport, AsyncClient
from planforge.models.occurrence import Occurrence
from planforge.models.setting import Setting
from sqlalchemy import func, select


async def test_view_get_does_not_create_occurrences(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/routines",
            json={
                "title": "Silent routine",
                "days_of_week": [0, 1, 2, 3, 4],
                "starts_on": "2026-07-21",
            },
        )
        assert create_response.status_code == 201

        session = test_app.state.session_factory()
        try:
            before = session.scalar(select(func.count()).select_from(Occurrence)) or 0
        finally:
            session.close()

        for path, params in (
            ("/api/views/today", {"date": "2026-07-21"}),
            ("/api/views/week", {"week_start": "2026-07-20"}),
            ("/api/views/month", {"month": "2026-07"}),
        ):
            response = await client.get(path, params=params)
            assert response.status_code == 200

        session = test_app.state.session_factory()
        try:
            after = session.scalar(select(func.count()).select_from(Occurrence)) or 0
        finally:
            session.close()

    assert before == after


async def test_view_get_does_not_seed_settings(test_app) -> None:
    session = test_app.state.session_factory()
    try:
        before = session.scalar(select(func.count()).select_from(Setting)) or 0
    finally:
        session.close()

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/views/today", params={"date": "2026-07-21"})
        assert response.status_code == 200

    session = test_app.state.session_factory()
    try:
        after = session.scalar(select(func.count()).select_from(Setting)) or 0
    finally:
        session.close()

    assert before == after
