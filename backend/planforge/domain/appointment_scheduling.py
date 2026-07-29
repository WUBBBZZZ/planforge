"""Appointment date/time scheduling and calendar placement."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum

from planforge.core.exceptions import ValidationError
from planforge.domain.datetime_utils import as_utc_aware
from planforge.domain.local_date import LocalDate
from planforge.domain.timezone import get_timezone


class SpanSegment(StrEnum):
    """Position of an appointment within a multi-day calendar span."""

    SINGLE = "single"
    START = "start"
    MIDDLE = "middle"
    END = "end"


@dataclass(frozen=True)
class AppointmentScheduleInput:
    """Validated appointment schedule fields."""

    is_all_day: bool
    start_date: LocalDate
    end_date: LocalDate
    starts_at: datetime | None
    ends_at: datetime | None


def combine_local_datetime(
    day: LocalDate, clock_time: time, *, timezone_name: str
) -> datetime:
    """Combine a local calendar date and wall-clock time in the planner timezone."""
    tz = get_timezone(timezone_name)
    local = datetime.combine(day.to_date(), clock_time, tzinfo=tz)
    return local.astimezone(UTC)


def local_date_from_instant(instant: datetime, *, timezone_name: str) -> LocalDate:
    """Return the planner-local calendar date for a UTC-aware instant."""
    local = as_utc_aware(instant).astimezone(get_timezone(timezone_name))
    return LocalDate(local.year, local.month, local.day)


def validate_all_day_schedule(*, start_date: LocalDate, end_date: LocalDate) -> None:
    """All-day end_date is inclusive and must not precede start_date."""
    if end_date.to_date() < start_date.to_date():
        raise ValidationError("End date must be on or after start date")


def validate_timed_schedule(
    *,
    starts_at: datetime,
    ends_at: datetime,
    timezone_name: str,
) -> tuple[LocalDate, LocalDate]:
    """Timed events must end strictly after they start."""
    start_utc = as_utc_aware(starts_at)
    end_utc = as_utc_aware(ends_at)
    if end_utc <= start_utc:
        raise ValidationError("End time must be after start time")
    start_date = local_date_from_instant(start_utc, timezone_name=timezone_name)
    end_date = local_date_from_instant(end_utc, timezone_name=timezone_name)
    return start_date, end_date


def build_schedule_input(
    *,
    is_all_day: bool,
    start_date: LocalDate,
    end_date: LocalDate,
    starts_at: datetime | None,
    ends_at: datetime | None,
    timezone_name: str,
) -> AppointmentScheduleInput:
    """Validate and normalize appointment schedule input."""
    if is_all_day:
        validate_all_day_schedule(start_date=start_date, end_date=end_date)
        if starts_at is not None or ends_at is not None:
            raise ValidationError(
                "All-day appointments must not include timed instants"
            )
        return AppointmentScheduleInput(
            is_all_day=True,
            start_date=start_date,
            end_date=end_date,
            starts_at=None,
            ends_at=None,
        )

    if starts_at is None or ends_at is None:
        raise ValidationError("Timed appointments require start and end instants")
    resolved_start, resolved_end = validate_timed_schedule(
        starts_at=starts_at,
        ends_at=ends_at,
        timezone_name=timezone_name,
    )
    if resolved_start.to_date() < start_date.to_date():
        raise ValidationError("Start instant must fall on the provided start date")
    if resolved_end.to_date() > end_date.to_date():
        raise ValidationError(
            "End instant must fall on or before the provided end date"
        )
    return AppointmentScheduleInput(
        is_all_day=False,
        start_date=start_date,
        end_date=end_date,
        starts_at=as_utc_aware(starts_at),
        ends_at=as_utc_aware(ends_at),
    )


def iter_span_dates(start_date: LocalDate, end_date: LocalDate) -> list[LocalDate]:
    """Return each inclusive local date between start_date and end_date."""
    dates: list[LocalDate] = []
    current = start_date
    while current.to_date() <= end_date.to_date():
        dates.append(current)
        current = current.add_days(1)
    return dates


def span_segment_for_day(
    day: LocalDate,
    *,
    start_date: LocalDate,
    end_date: LocalDate,
) -> SpanSegment:
    """Return how an appointment should render on a given calendar day."""
    if start_date.to_date() == end_date.to_date():
        return SpanSegment.SINGLE
    if day.to_date() == start_date.to_date():
        return SpanSegment.START
    if day.to_date() == end_date.to_date():
        return SpanSegment.END
    return SpanSegment.MIDDLE


def local_dates_for_schedule(
    *,
    is_all_day: bool,
    start_date: LocalDate,
    end_date: LocalDate,
    starts_at: datetime | None,
    ends_at: datetime | None,
    timezone_name: str,
) -> list[LocalDate]:
    """Return each planner-local day an appointment occupies."""
    if is_all_day:
        return iter_span_dates(start_date, end_date)

    assert starts_at is not None and ends_at is not None
    start_day = local_date_from_instant(starts_at, timezone_name=timezone_name)
    end_day = local_date_from_instant(ends_at, timezone_name=timezone_name)
    return iter_span_dates(start_day, end_day)


def appointment_times_iso(
    *,
    is_all_day: bool,
    starts_at: datetime | None,
    ends_at: datetime | None,
) -> tuple[str | None, str | None]:
    """Serialize timed instants for API responses."""
    if is_all_day or starts_at is None or ends_at is None:
        return None, None
    return (
        as_utc_aware(starts_at).astimezone(UTC).isoformat(),
        as_utc_aware(ends_at).astimezone(UTC).isoformat(),
    )


def appointment_overlaps_day(
    *,
    is_all_day: bool,
    start_date: date,
    end_date: date,
    starts_at: datetime | None,
    ends_at: datetime | None,
    day: LocalDate,
    timezone_name: str,
) -> bool:
    """Return True when the appointment occupies the given local day."""
    schedule_start = LocalDate.from_date(start_date)
    schedule_end = LocalDate.from_date(end_date)
    if is_all_day:
        return schedule_start.to_date() <= day.to_date() <= schedule_end.to_date()

    assert starts_at is not None and ends_at is not None
    day_start, day_end = _local_day_bounds(day, timezone_name=timezone_name)
    start_utc = as_utc_aware(starts_at)
    end_utc = as_utc_aware(ends_at)
    return start_utc < day_end and end_utc > day_start


def _local_day_bounds(
    day: LocalDate, *, timezone_name: str
) -> tuple[datetime, datetime]:
    tz = get_timezone(timezone_name)
    start = datetime.combine(day.to_date(), time.min, tzinfo=tz)
    end = start + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)
