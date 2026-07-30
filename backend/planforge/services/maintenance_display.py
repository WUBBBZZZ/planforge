"""Maintenance placement rules for planner calendar views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from planforge.domain.enums import MaintenanceNextActionStatus, ViewItemKind
from planforge.domain.local_date import LocalDate
from planforge.models.maintenance import MaintenanceDefinition
from planforge.services.display_date import (
    is_browsing_future_day,
    is_item_overdue,
    overdue_evaluation_date,
    rolled_display_date,
)

WEEK_UPCOMING_HORIZON_DAYS = 14
MONTH_UPCOMING_HORIZON_DAYS = 60


@dataclass(frozen=True)
class MaintenancePlacement:
    target: Literal["day", "upcoming"]
    display_date: LocalDate | None
    kind: ViewItemKind
    item_id: str
    title: str
    due_date: LocalDate
    is_overdue: bool


def schedule_by_date(maintenance: MaintenanceDefinition) -> LocalDate | None:
    """Return the date maintenance should be scheduled by (lead window start)."""
    if maintenance.next_due_date is None:
        return None
    due = LocalDate.from_date(maintenance.next_due_date)
    return due.add_days(-maintenance.lead_time_days)


def upcoming_horizon_days(*, view: Literal["week", "month"]) -> int:
    if view == "week":
        return WEEK_UPCOMING_HORIZON_DAYS
    return MONTH_UPCOMING_HORIZON_DAYS


def _is_browsing_future_period(*, period_end: LocalDate, clock_today: LocalDate) -> bool:
    return period_end > clock_today


def placements_for_maintenance(
    maintenance: MaintenanceDefinition,
    *,
    period_start: LocalDate,
    period_end: LocalDate,
    clock_today: LocalDate,
    view: Literal["week", "month"],
) -> list[MaintenancePlacement]:
    """Return where a maintenance item should appear in a week/month view."""
    if maintenance.next_due_date is None:
        return []

    due = LocalDate.from_date(maintenance.next_due_date)
    browsing_future = _is_browsing_future_period(
        period_end=period_end,
        clock_today=clock_today,
    )
    overdue_today = overdue_evaluation_date(
        reference_date=period_end,
        clock_today=clock_today,
    )

    if maintenance.next_action is MaintenanceNextActionStatus.SCHEDULED:
        return []

    if maintenance.next_action not in {
        MaintenanceNextActionStatus.NEEDS_SCHEDULING,
        MaintenanceNextActionStatus.REMINDER_SET,
    }:
        return []

    placements: list[MaintenancePlacement] = []

    if browsing_future:
        if period_start <= due <= period_end:
            placements.append(
                MaintenancePlacement(
                    target="day",
                    display_date=due,
                    kind=ViewItemKind.MAINTENANCE,
                    item_id=maintenance.id,
                    title=maintenance.title,
                    due_date=due,
                    is_overdue=False,
                )
            )
    else:
        display = rolled_display_date(due=due, today=overdue_today)
        if period_start <= display <= period_end:
            placements.append(
                MaintenancePlacement(
                    target="day",
                    display_date=display,
                    kind=ViewItemKind.MAINTENANCE,
                    item_id=maintenance.id,
                    title=maintenance.title,
                    due_date=due,
                    is_overdue=is_item_overdue(scheduled=due, today=overdue_today),
                )
            )

    lead_start = due.add_days(-maintenance.lead_time_days)
    horizon_end = period_end.add_days(upcoming_horizon_days(view=view))
    if due > period_end and due <= horizon_end and lead_start <= period_end:
        placements.append(
            MaintenancePlacement(
                target="upcoming",
                display_date=None,
                kind=ViewItemKind.MAINTENANCE,
                item_id=maintenance.id,
                title=maintenance.title,
                due_date=due,
                is_overdue=False,
            )
        )

    return placements


def should_show_maintenance_on_day(
    maintenance: MaintenanceDefinition,
    *,
    reference_date: LocalDate,
    clock_today: LocalDate,
) -> bool:
    """Return whether maintenance should appear on a single-day (Today) view."""
    if maintenance.next_due_date is None:
        return False
    if maintenance.next_action is MaintenanceNextActionStatus.SCHEDULED:
        return False
    if maintenance.next_action not in {
        MaintenanceNextActionStatus.NEEDS_SCHEDULING,
        MaintenanceNextActionStatus.REMINDER_SET,
    }:
        return False

    due = LocalDate.from_date(maintenance.next_due_date)
    if is_browsing_future_day(reference_date=reference_date, clock_today=clock_today):
        return due == reference_date

    overdue_today = overdue_evaluation_date(
        reference_date=reference_date,
        clock_today=clock_today,
    )
    lead_start = due.add_days(-maintenance.lead_time_days)
    display = rolled_display_date(due=due, today=overdue_today)
    return lead_start <= reference_date and reference_date >= display
