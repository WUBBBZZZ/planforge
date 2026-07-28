"""Routine occurrence generation."""

import json
from datetime import timedelta

from planforge.domain.local_date import LocalDate
from planforge.models.routine import Routine

SCHEDULE_WEEKLY = "weekly"
SCHEDULE_MONTHLY = "monthly"


def parse_days_of_week(raw: str) -> list[int]:
    """Parse stored weekday list (Monday=0)."""
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("days_of_week must be a JSON list")
    return [int(day) for day in parsed]


def routine_effective_start(routine: Routine) -> LocalDate:
    """Earliest calendar day this routine should have applied."""
    if routine.starts_on is not None:
        return LocalDate.from_date(routine.starts_on)
    return LocalDate.from_date(routine.created_at.date())


def iter_weekly_dates(
    *,
    start: LocalDate,
    end: LocalDate,
    days_of_week: list[int],
    interval_weeks: int,
    anchor: LocalDate,
) -> list[LocalDate]:
    """Return dates between start and end on selected weekdays every N weeks."""
    if interval_weeks < 1:
        interval_weeks = 1
    dates: list[LocalDate] = []
    current = start
    end_date = end.to_date()
    anchor_date = anchor.to_date()
    while current.to_date() <= end_date:
        if current.weekday() in days_of_week:
            weeks_since_anchor = (current.to_date() - anchor_date).days // 7
            if weeks_since_anchor >= 0 and weeks_since_anchor % interval_weeks == 0:
                dates.append(current)
        current = current.add_days(1)
    return dates


def iter_monthly_dates(
    *,
    start: LocalDate,
    end: LocalDate,
    day_of_month: int,
) -> list[LocalDate]:
    """Return calendar dates on a fixed day-of-month between start and end."""
    if day_of_month < 1:
        day_of_month = 1
    dates: list[LocalDate] = []
    cursor = start.start_of_month()
    end_date = end.to_date()
    while cursor.to_date() <= end_date:
        month_end = cursor.end_of_month()
        scheduled_day = min(day_of_month, month_end.day)
        candidate = LocalDate(cursor.year, cursor.month, scheduled_day)
        if start <= candidate <= end:
            dates.append(candidate)
        cursor = cursor.add_months(1)
    return dates


def iter_schedule_dates(
    *,
    start: LocalDate,
    end: LocalDate,
    days_of_week: list[int],
) -> list[LocalDate]:
    """Return local dates between start and end matching weekdays (legacy helper)."""
    dates: list[LocalDate] = []
    current = start.to_date()
    end_date = end.to_date()
    while current <= end_date:
        if current.weekday() in days_of_week:
            dates.append(LocalDate.from_date(current))
        current += timedelta(days=1)
    return dates


def schedule_dates_for_routine(
    *,
    routine: Routine,
    start: LocalDate,
    end: LocalDate,
) -> list[LocalDate]:
    """Return scheduled dates for a routine within an inclusive range."""
    if routine.schedule_type == SCHEDULE_MONTHLY:
        day_of_month = routine.day_of_month or 1
        return iter_monthly_dates(start=start, end=end, day_of_month=day_of_month)

    days = parse_days_of_week(routine.days_of_week)
    interval_weeks = routine.interval_weeks or 1
    anchor = routine_effective_start(routine)
    return iter_weekly_dates(
        start=start,
        end=end,
        days_of_week=days,
        interval_weeks=interval_weeks,
        anchor=anchor,
    )


def horizon_end(*, today: LocalDate, horizon_days: int) -> LocalDate:
    """Return the inclusive end date for occurrence generation."""
    return today.add_days(horizon_days)
