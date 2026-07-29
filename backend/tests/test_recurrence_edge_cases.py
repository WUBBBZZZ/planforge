"""Additional recurrence edge-case coverage."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.local_date import LocalDate
from planforge.services import routine_service
from planforge.services.occurrence_generator import (
    iter_monthly_dates,
    iter_weekly_dates,
    schedule_dates_for_routine,
)


def test_monthly_jan_31_clamps_to_february(db_session) -> None:
    dates = iter_monthly_dates(
        start=LocalDate.from_iso("2026-01-31"),
        end=LocalDate.from_iso("2026-03-31"),
        day_of_month=31,
    )
    assert [date.to_iso() for date in dates] == [
        "2026-01-31",
        "2026-02-28",
        "2026-03-31",
    ]


def test_biweekly_anchor_skips_off_weeks() -> None:
    dates = iter_weekly_dates(
        start=LocalDate.from_iso("2026-07-01"),
        end=LocalDate.from_iso("2026-07-31"),
        days_of_week=[3],
        interval_weeks=2,
        anchor=LocalDate.from_iso("2026-07-02"),
    )
    assert [date.to_iso() for date in dates] == [
        "2026-07-02",
        "2026-07-16",
        "2026-07-30",
    ]


def test_schedule_dates_for_monthly_routine_respects_horizon(db_session) -> None:
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Quarterly review",
        schedule_type="monthly",
        day_of_month=15,
        clock_today=LocalDate.from_iso("2026-07-15"),
    )
    dates = schedule_dates_for_routine(
        routine=routine,
        start=LocalDate.from_iso("2026-07-15"),
        end=LocalDate.from_iso("2026-08-29"),
    )
    assert dates
    assert all(date <= LocalDate.from_iso("2026-08-29") for date in dates)
