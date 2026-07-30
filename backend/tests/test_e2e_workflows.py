"""End-to-end workflow tests across API boundaries."""

from httpx import ASGITransport, AsyncClient


async def test_task_capture_to_today_completion_flow(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        today = (await client.get("/api/views/today")).json()["reference_date"]
        task = (
            await client.post(
                "/api/tasks",
                json={"title": "Water demo plants", "due_date": today},
            )
        ).json()
        await client.post(f"/api/tasks/{task['id']}/complete")
        today_items = (
            await client.get("/api/views/today", params={"date": today})
        ).json()

    titles = [item["title"] for item in today_items["items"]]
    assert "Water demo plants" in titles
    completed = next(
        item for item in today_items["items"] if item["title"] == "Water demo plants"
    )
    assert completed["is_completed"] is True


async def test_routine_occurrence_completion_flow(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/routines",
            json={
                "title": "Thursday sheets",
                "schedule_type": "weekly",
                "days_of_week": [3],
                "interval_weeks": 1,
            },
        )
        groups = (await client.get("/api/routine-groups")).json()
        misc_group = next(group for group in groups if group["name"] == "Misc")
        await client.patch(
            f"/api/routine-groups/{misc_group['id']}",
            json={"week_visible": True},
        )
        await client.post("/api/routines/sync-occurrences")
        week = (await client.get("/api/views/week")).json()
        occurrence_item = next(
            item
            for day in week["days"]
            for item in day["items"]
            if item["kind"] == "occurrence"
        )
        await client.post(
            f"/api/routines/occurrences/{occurrence_item['item_id']}/complete"
        )
        week_after = (await client.get("/api/views/week")).json()

    routine_titles = [
        item.get("routine_title")
        for day in week_after["days"]
        for item in day["items"]
        if item["kind"] == "occurrence"
    ]
    assert "Thursday sheets" in routine_titles


async def test_appointment_schedule_reschedule_cancel_flow(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        appointment = (
            await client.post(
                "/api/appointments",
                json={
                    "title": "Dentist demo",
                    "is_all_day": True,
                    "start_date": "2026-10-04",
                    "end_date": "2026-10-04",
                },
            )
        ).json()
        await client.post(
            f"/api/appointments/{appointment['id']}/reschedule",
            json={
                "is_all_day": True,
                "start_date": "2026-10-11",
                "end_date": "2026-10-11",
            },
        )
        month = (
            await client.get(
                "/api/views/month",
                params={"month": "2026-10"},
            )
        ).json()
        await client.post(f"/api/appointments/{appointment['id']}/cancel")
        cancelled = (await client.get(f"/api/appointments/{appointment['id']}")).json()

    month_titles = [item["title"] for day in month["days"] for item in day["items"]]
    assert "Dentist demo" in month_titles
    assert cancelled["status"] == "cancelled"


async def test_maintenance_complete_schedule_flow(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        maintenance = (
            await client.post(
                "/api/maintenance",
                json={
                    "title": "Oil change demo",
                    "interval_unit": "months",
                    "interval_value": 6,
                },
            )
        ).json()
        await client.post(
            f"/api/maintenance/{maintenance['id']}/complete",
            json={"completed_on": "2026-06-12"},
        )
        detail = (
            await client.post(
                f"/api/maintenance/{maintenance['id']}/schedule-appointment",
                json={
                    "is_all_day": True,
                    "start_date": "2026-12-01",
                    "end_date": "2026-12-01",
                },
            )
        ).json()
        board = (await client.get("/api/maintenance/history-board")).json()

    assert detail["linked_appointment"] is not None
    assert detail["next_action_status"] == "scheduled"
    assert board["rows"][0]["completions"][0]["completed_on"] == "2026-06-12"
