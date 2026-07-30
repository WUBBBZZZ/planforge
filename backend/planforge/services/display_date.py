"""Display-date helpers for planner views."""

from planforge.domain.local_date import LocalDate


def is_item_overdue(*, scheduled: LocalDate, today: LocalDate) -> bool:
    """Return True when today is after the scheduled calendar day.

    Items stay not-overdue through the entire day they are due; overdue begins
    on the following calendar day if still incomplete.
    """
    return today > scheduled


def overdue_evaluation_date(
    *,
    reference_date: LocalDate,
    clock_today: LocalDate,
) -> LocalDate:
    """Return the date used for overdue and roll-forward when browsing days.

    When viewing a future day, prior unmarked work is treated as complete, so
    overdue logic stays anchored to the real current day.
    """
    return clock_today if reference_date > clock_today else reference_date


def is_browsing_future_day(
    *,
    reference_date: LocalDate,
    clock_today: LocalDate,
) -> bool:
    """Return True when the user is viewing a day after the real current day."""
    return reference_date > clock_today


def rolled_display_date(*, due: LocalDate, today: LocalDate) -> LocalDate:
    """Return the calendar day where a pending item should appear.

    Items due on or after ``today`` stay on their due date. Older pending items
    roll forward to ``today`` so missed work surfaces on the current day instead
    of cluttering the original due date or the start of a future week.
    """
    if is_item_overdue(scheduled=due, today=today):
        return today
    return due
