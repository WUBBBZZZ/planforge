"""Tests for LocalDate."""

import pytest
from planforge.domain.local_date import InvalidLocalDateError, LocalDate


def test_from_iso_parses_valid_date() -> None:
    value = LocalDate.from_iso("2026-07-21")
    assert value.year == 2026
    assert value.month == 7
    assert value.day == 21
    assert value.to_iso() == "2026-07-21"


def test_invalid_iso_raises() -> None:
    with pytest.raises(InvalidLocalDateError):
        LocalDate.from_iso("2026-02-30")


def test_ordering() -> None:
    earlier = LocalDate.from_iso("2026-07-20")
    later = LocalDate.from_iso("2026-07-21")
    assert earlier < later
