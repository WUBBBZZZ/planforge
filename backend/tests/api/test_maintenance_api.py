"""API tests for maintenance."""

from httpx import ASGITransport, AsyncClient


async def test_maintenance_lifecycle_api(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/maintenance",
            json={
                "title": "Dentist",
                "interval_unit": "months",
                "interval_value": 6,
            },
        )
        maintenance_id = create_response.json()["id"]
        await client.post(
            f"/api/maintenance/{maintenance_id}/complete",
            json={"completed_on": "2026-07-27"},
        )
        schedule_response = await client.post(
            f"/api/maintenance/{maintenance_id}/schedule-appointment",
            json={
                "is_all_day": False,
                "start_date": "2026-10-04",
                "end_date": "2026-10-04",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
            },
        )
        appointment_id = schedule_response.json()["linked_appointment"]["id"]
        await client.post(f"/api/appointments/{appointment_id}/cancel")
        detail_response = await client.get(f"/api/maintenance/{maintenance_id}")

    detail = detail_response.json()
    assert detail["next_action_status"] == "needs_scheduling"
    assert detail["linked_appointment"] is None


async def test_history_board_api(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/maintenance",
            json={"title": "Physical", "interval_unit": "years", "interval_value": 1},
        )
        maintenance_id = create_response.json()["id"]
        await client.post(
            f"/api/maintenance/{maintenance_id}/completions",
            json={"completed_on": "2025-07-08"},
        )
        await client.post(
            f"/api/maintenance/{maintenance_id}/completions",
            json={"completed_on": "2026-07-12"},
        )
        board_response = await client.get("/api/maintenance/history-board")

    board = board_response.json()
    row = next(r for r in board["rows"] if r["maintenance"]["title"] == "Physical")
    assert row["completions"][0]["completed_on"] == "2026-07-12"


async def test_scheduling_reminder_api(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/maintenance",
            json={
                "title": "Oil change",
                "interval_unit": "months",
                "interval_value": 4,
            },
        )
        maintenance_id = create_response.json()["id"]
        await client.post(
            f"/api/maintenance/{maintenance_id}/complete",
            json={"completed_on": "2026-06-12"},
        )
        reminder_response = await client.post(
            f"/api/maintenance/{maintenance_id}/scheduling-reminder",
            json={"reminder_date": "2026-09-01"},
        )

    assert reminder_response.json()["next_action_status"] == "reminder_set"
