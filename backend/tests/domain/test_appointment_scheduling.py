"""Domain tests for appointment scheduling."""

from datetime import UTC, datetime, time

import pytest
from planforge.core.exceptions import ValidationError
from planforge.domain.appointment_scheduling import (
    SpanSegment,
    build_schedule_input,
    combine_local_datetime,
    iter_span_dates,
    local_date_from_instant,
    local_dates_for_schedule,
    span_segment_for_day,
)
from planforge.domain.local_date import LocalDate

PACIFIC = "America/Los_Angeles"
EASTERN = "America/New_York"


def test_all_day_inclusive_span_dates() -> None:
    start = LocalDate.from_iso("2026-07-21")
    end = LocalDate.from_iso("2026-07-25")
    dates = iter_span_dates(start, end)
    assert [day.to_iso() for day in dates] == [
        "2026-07-21",
        "2026-07-22",
        "2026-07-23",
        "2026-07-24",
        "2026-07-25",
    ]


def test_all_day_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError, match="End date"):
        build_schedule_input(
            is_all_day=True,
            start_date=LocalDate.from_iso("2026-07-22"),
            end_date=LocalDate.from_iso("2026-07-21"),
            starts_at=None,
            ends_at=None,
            timezone_name=PACIFIC,
        )


def test_timed_rejects_equal_start_and_end() -> None:
    instant = datetime(2026, 7, 21, 15, 0, tzinfo=UTC)
    with pytest.raises(ValidationError, match="after start"):
        build_schedule_input(
            is_all_day=False,
            start_date=LocalDate.from_iso("2026-07-21"),
            end_date=LocalDate.from_iso("2026-07-21"),
            starts_at=instant,
            ends_at=instant,
            timezone_name=PACIFIC,
        )


def test_all_day_has_no_timed_instants() -> None:
    with pytest.raises(ValidationError, match="must not include timed"):
        build_schedule_input(
            is_all_day=True,
            start_date=LocalDate.from_iso("2026-07-21"),
            end_date=LocalDate.from_iso("2026-07-21"),
            starts_at=datetime(2026, 7, 21, 15, 0, tzinfo=UTC),
            ends_at=datetime(2026, 7, 21, 16, 0, tzinfo=UTC),
            timezone_name=PACIFIC,
        )


def test_timed_dst_spring_forward_local_date() -> None:
    # 2026-03-08 12:30 UTC = 07:30 EST (before DST) on March 8 in New York.
    starts_at = combine_local_datetime(
        LocalDate.from_iso("2026-03-08"),
        time(7, 30),
        timezone_name=EASTERN,
    )
    local_day = local_date_from_instant(starts_at, timezone_name=EASTERN)
    assert local_day.to_iso() == "2026-03-08"


def test_timed_cross_midnight_local_dates() -> None:
    starts_at = combine_local_datetime(
        LocalDate.from_iso("2026-07-21"),
        time(22, 0),
        timezone_name=PACIFIC,
    )
    ends_at = combine_local_datetime(
        LocalDate.from_iso("2026-07-22"),
        time(1, 0),
        timezone_name=PACIFIC,
    )
    dates = local_dates_for_schedule(
        is_all_day=False,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-22"),
        starts_at=starts_at,
        ends_at=ends_at,
        timezone_name=PACIFIC,
    )
    assert [day.to_iso() for day in dates] == ["2026-07-21", "2026-07-22"]


def test_span_segment_positions() -> None:
    start = LocalDate.from_iso("2026-07-21")
    end = LocalDate.from_iso("2026-07-23")
    assert (
        span_segment_for_day(start, start_date=start, end_date=end) is SpanSegment.START
    )
    assert (
        span_segment_for_day(start.add_days(1), start_date=start, end_date=end)
        is SpanSegment.MIDDLE
    )
    assert span_segment_for_day(end, start_date=start, end_date=end) is SpanSegment.END
