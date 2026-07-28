"""Week boundary helpers."""

from datetime import timedelta

from planforge.domain.local_date import LocalDate

_WEEKDAY_BY_NAME = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def week_bounds(
    *,
    reference_date: LocalDate,
    week_start_day: str,
) -> tuple[LocalDate, LocalDate]:
    """Return inclusive week start and end dates for the reference date."""
    start_weekday = _WEEKDAY_BY_NAME[week_start_day]
    current = reference_date.to_date()
    delta_days = (current.weekday() - start_weekday) % 7
    week_start = current - timedelta(days=delta_days)
    week_end = week_start + timedelta(days=6)
    return LocalDate.from_date(week_start), LocalDate.from_date(week_end)
