"""Integration tests between appointments and maintenance."""

from httpx import ASGITransport, AsyncClient


async def test_schedule_link_reschedule_and_cancel_maintenance_appointment(
    test_app,
) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        maintenance = (
            await client.post(
                "/api/maintenance",
                json={
                    "title": "Dentist demo",
                    "interval_unit": "months",
                    "interval_value": 6,
                },
            )
        ).json()
        await client.post(
            f"/api/maintenance/{maintenance['id']}/complete",
            json={"completed_on": "2026-07-27"},
        )
        scheduled = (
            await client.post(
                f"/api/maintenance/{maintenance['id']}/schedule-appointment",
                json={
                    "is_all_day": True,
                    "start_date": "2026-10-04",
                    "end_date": "2026-10-04",
                },
            )
        ).json()
        appointment_id = scheduled["linked_appointment"]["id"]

        duplicate = await client.post(
            f"/api/maintenance/{maintenance['id']}/schedule-appointment",
            json={
                "is_all_day": True,
                "start_date": "2026-11-01",
                "end_date": "2026-11-01",
            },
        )
        assert duplicate.status_code == 409

        await client.post(
            f"/api/maintenance/{maintenance['id']}/reschedule-appointment",
            json={
                "is_all_day": True,
                "start_date": "2026-10-18",
                "end_date": "2026-10-18",
            },
        )
        appointment = (await client.get(f"/api/appointments/{appointment_id}")).json()
        assert appointment["start_date"] == "2026-10-18"

        await client.post(f"/api/appointments/{appointment_id}/cancel")
        maintenance_after = (
            await client.get(f"/api/maintenance/{maintenance['id']}")
        ).json()

    assert maintenance_after["linked_appointment_id"] is None
    assert maintenance_after["next_action_status"] == "needs_scheduling"
    assert maintenance_after["last_completed_date"] == "2026-07-27"


async def test_scheduling_reminder_does_not_create_appointment(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        maintenance = (
            await client.post(
                "/api/maintenance",
                json={
                    "title": "Physical demo",
                    "interval_unit": "years",
                    "interval_value": 1,
                },
            )
        ).json()
        await client.post(
            f"/api/maintenance/{maintenance['id']}/complete",
            json={"completed_on": "2026-07-12"},
        )
        reminded = (
            await client.post(
                f"/api/maintenance/{maintenance['id']}/scheduling-reminder",
                json={"reminder_date": "2026-09-01"},
            )
        ).json()
        appointments = (await client.get("/api/appointments")).json()

    assert reminded["next_action_status"] == "reminder_set"
    assert reminded["scheduling_reminder_date"] == "2026-09-01"
    assert appointments == []
