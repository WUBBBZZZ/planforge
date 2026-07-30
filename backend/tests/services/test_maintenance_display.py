"""Tests for maintenance display placement."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import MaintenanceNextActionStatus
from planforge.domain.local_date import LocalDate
from planforge.models.maintenance import MaintenanceDefinition
from planforge.services.maintenance_display import placements_for_maintenance


def _maintenance(
    *,
    due: str,
    lead_time_days: int = 30,
    next_action: str = MaintenanceNextActionStatus.NEEDS_SCHEDULING.value,
) -> MaintenanceDefinition:
    return MaintenanceDefinition(
        owner_id=LOCAL_OWNER_ID,
        title="Oil change",
        interval_unit="months",
        interval_value=6,
        next_due_date=LocalDate.from_iso(due).to_date(),
        lead_time_days=lead_time_days,
        next_action_status=next_action,
        status="active",
    )


def test_maintenance_upcoming_respects_lead_window_and_horizon() -> None:
    item = _maintenance(due="2026-09-15", lead_time_days=30)
    placements = placements_for_maintenance(
        item,
        period_start=LocalDate.from_iso("2026-07-01"),
        period_end=LocalDate.from_iso("2026-07-31"),
        clock_today=LocalDate.from_iso("2026-07-21"),
        view="month",
    )
    assert placements == []

    august_placements = placements_for_maintenance(
        item,
        period_start=LocalDate.from_iso("2026-08-01"),
        period_end=LocalDate.from_iso("2026-08-31"),
        clock_today=LocalDate.from_iso("2026-07-21"),
        view="month",
    )
    assert len(august_placements) == 1
    assert august_placements[0].target == "upcoming"


def test_scheduled_maintenance_omitted_from_planner() -> None:
    item = _maintenance(
        due="2026-08-15",
        next_action=MaintenanceNextActionStatus.SCHEDULED.value,
    )
    placements = placements_for_maintenance(
        item,
        period_start=LocalDate.from_iso("2026-08-01"),
        period_end=LocalDate.from_iso("2026-08-31"),
        clock_today=LocalDate.from_iso("2026-07-21"),
        view="month",
    )
    assert placements == []
