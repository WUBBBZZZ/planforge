"""API tests for appointments."""

from httpx import ASGITransport, AsyncClient


async def test_create_timed_appointment_api(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/appointments",
            json={
                "title": "Doctor",
                "is_all_day": False,
                "start_date": "2026-07-21",
                "end_date": "2026-07-21",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
                "location": "Clinic",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Doctor"
    assert payload["status"] == "scheduled"
    assert payload["starts_at"] is not None


async def test_create_all_day_multi_day_api(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/appointments",
            json={
                "title": "Vacation",
                "is_all_day": True,
                "start_date": "2026-07-21",
                "end_date": "2026-07-25",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["is_all_day"] is True
    assert payload["starts_at"] is None
    assert payload["end_date"] == "2026-07-25"


async def test_appointment_lifecycle_api(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/appointments",
            json={
                "title": "Flight",
                "is_all_day": False,
                "start_date": "2026-07-21",
                "end_date": "2026-07-21",
                "start_time": "08:00:00",
                "end_time": "11:00:00",
            },
        )
        appointment_id = create_response.json()["id"]
        await client.patch(
            f"/api/appointments/{appointment_id}",
            json={"location": "SFO"},
        )
        await client.post(
            f"/api/appointments/{appointment_id}/reschedule",
            json={
                "is_all_day": True,
                "start_date": "2026-07-22",
                "end_date": "2026-07-22",
            },
        )
        cancel_response = await client.post(
            f"/api/appointments/{appointment_id}/cancel",
        )
        reopen_response = await client.post(
            f"/api/appointments/{appointment_id}/reopen",
        )

    assert cancel_response.json()["status"] == "cancelled"
    assert reopen_response.json()["status"] == "scheduled"


async def test_invalid_range_returns_422(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/appointments",
            json={
                "title": "Bad",
                "is_all_day": True,
                "start_date": "2026-07-25",
                "end_date": "2026-07-21",
            },
        )

    assert response.status_code == 422


async def test_appointment_appears_in_today_and_month_views(test_app) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/appointments",
            json={
                "title": "Trip",
                "is_all_day": True,
                "start_date": "2026-07-21",
                "end_date": "2026-07-23",
            },
        )
        today_response = await client.get(
            "/api/views/today",
            params={"date": "2026-07-22"},
        )
        month_response = await client.get(
            "/api/views/month",
            params={"month": "2026-07"},
        )

    today_items = [
        item for item in today_response.json()["items"] if item["kind"] == "appointment"
    ]
    assert len(today_items) == 1
    assert today_items[0]["span_segment"] == "middle"

    month_days = [
        group
        for group in month_response.json()["days"]
        if group["date"] in {"2026-07-21", "2026-07-22", "2026-07-23"}
    ]
    appointment_days = [
        day["date"]
        for day in month_days
        if any(item["kind"] == "appointment" for item in day["items"])
    ]
    assert appointment_days == ["2026-07-21", "2026-07-22", "2026-07-23"]
