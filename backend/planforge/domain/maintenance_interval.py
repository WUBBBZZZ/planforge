"""Calendar-aware maintenance interval calculations."""

from planforge.core.exceptions import ValidationError
from planforge.domain.enums import MaintenanceIntervalUnit
from planforge.domain.local_date import LocalDate


def add_interval(
    base: LocalDate,
    *,
    unit: MaintenanceIntervalUnit,
    value: int,
) -> LocalDate:
    """Advance a date by a maintenance interval using calendar semantics.

    Months and years use :meth:`LocalDate.add_months`, which clamps the
    day-of-month when needed (e.g. Jan 31 + 1 month -> Feb 28/29).
    """
    if value < 1:
        raise ValidationError("Interval value must be at least 1")
    if unit is MaintenanceIntervalUnit.DAYS:
        return base.add_days(value)
    if unit is MaintenanceIntervalUnit.WEEKS:
        return base.add_days(value * 7)
    if unit is MaintenanceIntervalUnit.MONTHS:
        return base.add_months(value)
    if unit is MaintenanceIntervalUnit.YEARS:
        return base.add_months(value * 12)
    raise ValidationError("Manual maintenance has no automatic interval")


def compute_next_due_date(
    last_completed: LocalDate,
    *,
    unit: MaintenanceIntervalUnit,
    value: int | None,
) -> LocalDate | None:
    """Return the next due date after a completion, or None when manual."""
    if unit is MaintenanceIntervalUnit.MANUAL:
        return None
    if value is None:
        raise ValidationError("Interval value is required for automatic schedules")
    return add_interval(last_completed, unit=unit, value=value)
