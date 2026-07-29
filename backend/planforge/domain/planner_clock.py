"""Planner clock backed by the user timezone preference."""

from datetime import datetime

from planforge.domain.local_date import LocalDate
from planforge.domain.timezone import get_timezone


class PlannerClock:
    """Resolve today's local date in the configured planner timezone."""

    def __init__(self, timezone_name: str) -> None:
        self._timezone_name = timezone_name

    @property
    def timezone_name(self) -> str:
        return self._timezone_name

    def today(self) -> LocalDate:
        now = datetime.now(get_timezone(self._timezone_name))
        return LocalDate(now.year, now.month, now.day)
