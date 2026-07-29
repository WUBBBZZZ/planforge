"""Domain tests for maintenance intervals."""

from planforge.domain.enums import MaintenanceIntervalUnit
from planforge.domain.local_date import LocalDate
from planforge.domain.maintenance_interval import add_interval, compute_next_due_date


def test_jan_31_plus_six_months_clamps_to_july_31() -> None:
    base = LocalDate.from_iso("2026-01-31")
    result = add_interval(base, unit=MaintenanceIntervalUnit.MONTHS, value=6)
    assert result.to_iso() == "2026-07-31"


def test_jan_31_plus_one_month_clamps_to_feb_end() -> None:
    base = LocalDate.from_iso("2026-01-31")
    result = add_interval(base, unit=MaintenanceIntervalUnit.MONTHS, value=1)
    assert result.to_iso() == "2026-02-28"


def test_manual_interval_returns_no_next_due() -> None:
    base = LocalDate.from_iso("2026-07-27")
    assert (
        compute_next_due_date(
            base,
            unit=MaintenanceIntervalUnit.MANUAL,
            value=None,
        )
        is None
    )


def test_years_use_calendar_months() -> None:
    base = LocalDate.from_iso("2024-02-29")
    result = add_interval(base, unit=MaintenanceIntervalUnit.YEARS, value=1)
    assert result.to_iso() == "2025-02-28"
