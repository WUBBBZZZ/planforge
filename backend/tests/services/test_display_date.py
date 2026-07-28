"""Tests for display date helpers."""

from planforge.domain.local_date import LocalDate
from planforge.services.display_date import is_item_overdue, rolled_display_date


def test_is_item_overdue_false_on_due_date() -> None:
    due = LocalDate.from_iso("2026-07-26")
    today = LocalDate.from_iso("2026-07-26")
    assert is_item_overdue(scheduled=due, today=today) is False


def test_is_item_overdue_true_day_after_due_date() -> None:
    due = LocalDate.from_iso("2026-07-26")
    today = LocalDate.from_iso("2026-07-27")
    assert is_item_overdue(scheduled=due, today=today) is True


def test_rolled_display_date_keeps_future_due_dates() -> None:
    due = LocalDate.from_iso("2026-07-28")
    today = LocalDate.from_iso("2026-07-26")
    assert rolled_display_date(due=due, today=today) == due


def test_rolled_display_date_moves_past_due_to_today() -> None:
    due = LocalDate.from_iso("2026-07-20")
    today = LocalDate.from_iso("2026-07-26")
    assert rolled_display_date(due=due, today=today) == today


def test_rolled_display_date_keeps_due_today() -> None:
    due = LocalDate.from_iso("2026-07-26")
    today = LocalDate.from_iso("2026-07-26")
    assert rolled_display_date(due=due, today=today) == due
