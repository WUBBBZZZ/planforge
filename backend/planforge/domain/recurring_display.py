"""Recurring occurrence display policy."""

from dataclasses import dataclass
from enum import StrEnum

from planforge.domain.local_date import LocalDate
from planforge.services.week_bounds import week_bounds


class RecurringDisplayMode(StrEnum):
    """How many pending routine occurrences to surface per routine."""

    CURRENT_ONLY = "current_only"
    CURRENT_PLUS_NEXT = "current_plus_next"
    CURRENT_WEEK_ONLY = "current_week_only"
    CURRENT_AND_NEXT_WEEK = "current_and_next_week"
    CUSTOM = "custom"


class OccurrenceDisplayRole(StrEnum):
    """Planner-facing position of a visible routine occurrence."""

    OVERDUE = "overdue"
    CURRENT = "current"
    NEXT = "next"


@dataclass(frozen=True)
class RecurringDisplayPolicy:
    """Display policy for recurring routine occurrences."""

    mode: RecurringDisplayMode = RecurringDisplayMode.CURRENT_PLUS_NEXT

    def horizon_bounds(
        self,
        *,
        today: LocalDate,
        week_start_day: str,
    ) -> tuple[LocalDate, LocalDate]:
        """Return inclusive horizon bounds for recurring occurrence display."""
        week_start, week_end = week_bounds(
            reference_date=today,
            week_start_day=week_start_day,
        )
        if self.mode is RecurringDisplayMode.CURRENT_WEEK_ONLY:
            return week_start, week_end
        # Default and current_plus_next: current calendar week plus the next week.
        return week_start, week_end.add_days(7)

    def max_following_occurrences(self) -> int:
        """Return how many non-overdue occurrences may appear after the first."""
        if self.mode is RecurringDisplayMode.CURRENT_ONLY:
            return 0
        if self.mode is RecurringDisplayMode.CURRENT_WEEK_ONLY:
            return 0
        return 1


DEFAULT_RECURRING_DISPLAY_POLICY = RecurringDisplayPolicy()
