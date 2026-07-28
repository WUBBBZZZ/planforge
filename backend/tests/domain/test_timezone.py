"""Tests for timezone helpers."""

from datetime import UTC

from planforge.domain.timezone import get_timezone


def test_get_timezone_utc_without_tzdata() -> None:
    tz = get_timezone("UTC")
    assert tz == UTC


def test_get_timezone_unknown_falls_back_to_utc() -> None:
    tz = get_timezone("Not/A_Real_Zone")
    assert tz == UTC
