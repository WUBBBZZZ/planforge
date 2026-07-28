"""Time source for planner views."""

from datetime import datetime
from typing import Protocol

from planforge.core.config import Settings, get_settings
from planforge.domain.local_date import LocalDate
from planforge.domain.timezone import get_timezone


class Clock(Protocol):
    """Provide today's local date in a configured timezone."""

    def today(self) -> LocalDate: ...

    def timezone_name(self) -> str: ...


class SystemClock:
    """Clock backed by the system time and configured IANA timezone."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def timezone_name(self) -> str:
        return self._settings.timezone

    def today(self) -> LocalDate:
        now = datetime.now(get_timezone(self.timezone_name()))
        return LocalDate(now.year, now.month, now.day)
