"""Tests for routine occurrence generation."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.local_date import LocalDate
from planforge.services import routine_service
from planforge.services.occurrence_generator import (
    SCHEDULE_MONTHLY,
    iter_monthly_dates,
    iter_weekly_dates,
    schedule_dates_for_routine,
)
from planforge.services.settings_service import PolicySnapshot


def test_weekly_every_thursday(db_session) -> None:
    dates = iter_weekly_dates(
        start=LocalDate.from_iso("2026-07-01"),
        end=LocalDate.from_iso("2026-07-31"),
        days_of_week=[3],
        interval_weeks=1,
        anchor=LocalDate.from_iso("2026-07-02"),
    )
    assert [date.to_iso() for date in dates] == [
        "2026-07-02",
        "2026-07-09",
        "2026-07-16",
        "2026-07-23",
        "2026-07-30",
    ]


def test_monthly_first_of_month(db_session) -> None:
    dates = iter_monthly_dates(
        start=LocalDate.from_iso("2026-01-01"),
        end=LocalDate.from_iso("2026-03-31"),
        day_of_month=1,
    )
    assert [date.to_iso() for date in dates] == [
        "2026-01-01",
        "2026-02-01",
        "2026-03-01",
    ]


def test_routine_does_not_backfill_before_start(db_session) -> None:
    clock_today = LocalDate.from_iso("2026-07-27")
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Thursday sheets",
        schedule_type="weekly",
        days_of_week=[3],
        interval_weeks=1,
        clock_today=clock_today,
    )
    policies = PolicySnapshot(routine_horizon_days=14)
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=clock_today,
        policies=policies,
    )
    pending = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )
    scheduled = [LocalDate.from_date(occurrence.scheduled_date) for occurrence, _ in pending]
    assert all(date >= clock_today for date in scheduled)
    assert scheduled[0].to_iso() == "2026-07-30"


def test_monthly_routine_schedules_calendar_day(db_session) -> None:
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Pay rent",
        schedule_type=SCHEDULE_MONTHLY,
        day_of_month=1,
        days_of_week=[0],
        clock_today=LocalDate.from_iso("2026-07-15"),
    )
    dates = schedule_dates_for_routine(
        routine=routine,
        start=LocalDate.from_iso("2026-07-15"),
        end=LocalDate.from_iso("2026-09-30"),
    )
    assert [date.to_iso() for date in dates] == ["2026-08-01", "2026-09-01"]
