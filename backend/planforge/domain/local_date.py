"""Calendar date without timezone."""

from dataclasses import dataclass
from datetime import date, timedelta


class InvalidLocalDateError(ValueError):
    """Raised when a date string or components are not a valid calendar date."""


@dataclass(frozen=True, order=True)
class LocalDate:
    """ISO calendar date (YYYY-MM-DD) with no time or timezone."""

    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        try:
            date(self.year, self.month, self.day)
        except ValueError as exc:
            raise InvalidLocalDateError(str(exc)) from exc

    @classmethod
    def from_iso(cls, value: str) -> LocalDate:
        """Parse an ISO date string."""
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise InvalidLocalDateError(f"Invalid ISO date: {value}") from exc
        return cls(parsed.year, parsed.month, parsed.day)

    @classmethod
    def from_date(cls, value: date) -> LocalDate:
        """Build from a standard library date."""
        return cls(value.year, value.month, value.day)

    def to_iso(self) -> str:
        """Return ISO YYYY-MM-DD."""
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

    def to_date(self) -> date:
        """Convert to a standard library date."""
        return date(self.year, self.month, self.day)

    def add_days(self, days: int) -> LocalDate:
        """Return a new date offset by the given number of days."""
        return LocalDate.from_date(self.to_date() + timedelta(days=days))

    def start_of_month(self) -> LocalDate:
        """Return the first day of this date's calendar month."""
        return LocalDate(self.year, self.month, 1)

    def end_of_month(self) -> LocalDate:
        """Return the last day of this date's calendar month."""
        if self.month == 12:
            return LocalDate(self.year + 1, 1, 1).add_days(-1)
        return LocalDate(self.year, self.month + 1, 1).add_days(-1)

    def add_months(self, months: int) -> LocalDate:
        """Return the same day-of-month offset by the given number of months."""
        month_index = (self.year * 12 + (self.month - 1)) + months
        year = month_index // 12
        month = (month_index % 12) + 1
        last_day = LocalDate(year, month, 1).end_of_month().day
        return LocalDate(year, month, min(self.day, last_day))

    def weekday(self) -> int:
        """Monday=0 .. Sunday=6 (matches datetime.date.weekday)."""
        return self.to_date().weekday()
