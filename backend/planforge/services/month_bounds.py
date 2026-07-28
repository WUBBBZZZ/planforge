"""Month boundary helpers."""

from planforge.domain.local_date import LocalDate


def month_bounds(*, reference_date: LocalDate) -> tuple[LocalDate, LocalDate]:
    """Return inclusive month start and end dates for the reference date."""
    month_start = reference_date.start_of_month()
    month_end = reference_date.end_of_month()
    return month_start, month_end


def month_key(reference_date: LocalDate) -> str:
    """Return YYYY-MM for the reference date's calendar month."""
    return f"{reference_date.year:04d}-{reference_date.month:02d}"
