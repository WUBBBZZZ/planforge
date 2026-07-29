"""Tests for UTC datetime normalization."""

from datetime import UTC, datetime

from planforge.domain.datetime_utils import as_utc_aware


def test_naive_datetime_treated_as_utc() -> None:
    naive = datetime(2026, 7, 21, 12, 0, 0)
    aware = as_utc_aware(naive)
    assert aware.tzinfo is UTC
    assert aware.hour == 12


def test_aware_datetime_converted_to_utc() -> None:
    from zoneinfo import ZoneInfo

    pacific = datetime(2026, 7, 21, 9, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
    aware = as_utc_aware(pacific)
    assert aware.tzinfo is UTC
    assert aware.hour == 16
