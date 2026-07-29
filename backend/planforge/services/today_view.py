"""Today view assembly."""

from dataclasses import dataclass

from planforge.domain.appointment_scheduling import (
    appointment_overlaps_day,
    appointment_times_iso,
)
from planforge.domain.enums import (
    AppointmentStatus,
    MaintenanceStatus,
    TaskStatus,
    ViewItemKind,
)
from planforge.domain.local_date import LocalDate
from planforge.domain.recurring_display import DEFAULT_RECURRING_DISPLAY_POLICY
from planforge.models.appointment import Appointment
from planforge.models.maintenance import MaintenanceDefinition
from planforge.models.task import Task
from planforge.services import routine_service
from planforge.services.completion_display import completed_items_for_local_day
from planforge.services.display_date import is_item_overdue, rolled_display_date
from planforge.services.recurring_occurrence_display import (
    select_visible_routine_occurrences,
)
from planforge.services.settings_service import PolicySnapshot
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class TodayItem:
    kind: ViewItemKind
    item_id: str
    title: str
    notes: str | None
    due_date: LocalDate | None
    starts_at: str | None
    ends_at: str | None
    is_overdue: bool
    routine_title: str | None = None
    is_completed: bool = False
    occurrence_role: str | None = None
    is_all_day: bool = False
    span_start_date: LocalDate | None = None
    span_end_date: LocalDate | None = None
    span_segment: str | None = None
    location: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class TodayView:
    reference_date: LocalDate
    items: list[TodayItem]


def assemble_today_view(
    *,
    session: Session,
    owner_id: str,
    reference_date: LocalDate,
    clock_today: LocalDate,
    policies: PolicySnapshot,
) -> TodayView:
    """Assemble items for the Today view."""
    ref = reference_date.to_date()
    items: list[TodayItem] = []

    tasks = list(
        session.scalars(
            select(Task).where(
                Task.owner_id == owner_id,
                Task.status == TaskStatus.PENDING.value,
                Task.due_date.is_not(None),
            )
        )
    )
    for task in tasks:
        assert task.due_date is not None
        due = LocalDate.from_date(task.due_date)
        if due.to_date() == ref:
            items.append(
                TodayItem(
                    kind=ViewItemKind.TASK,
                    item_id=task.id,
                    title=task.title,
                    notes=task.notes,
                    due_date=due,
                    starts_at=None,
                    ends_at=None,
                    is_overdue=False,
                )
            )
        elif policies.today_include_rolled_tasks and is_item_overdue(
            scheduled=due, today=reference_date
        ):
            items.append(
                TodayItem(
                    kind=ViewItemKind.TASK,
                    item_id=task.id,
                    title=task.title,
                    notes=task.notes,
                    due_date=due,
                    starts_at=None,
                    ends_at=None,
                    is_overdue=True,
                )
            )

    if policies.today_include_routine_occurrences:
        recurring_policy = DEFAULT_RECURRING_DISPLAY_POLICY
        horizon_start, horizon_end = recurring_policy.horizon_bounds(
            today=reference_date,
            week_start_day=policies.week_start_day,
        )
        for visible in select_visible_routine_occurrences(
            routine_service.list_pending_occurrences(session, owner_id=owner_id),
            today=reference_date,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            policy=recurring_policy,
            missed_behavior=policies.routine_missed_behavior,
        ):
            display = rolled_display_date(due=visible.scheduled, today=reference_date)
            if display.to_date() != ref:
                continue
            items.append(
                TodayItem(
                    kind=ViewItemKind.OCCURRENCE,
                    item_id=visible.occurrence.id,
                    title=visible.routine.title,
                    notes=visible.routine.notes,
                    due_date=visible.scheduled,
                    starts_at=None,
                    ends_at=None,
                    is_overdue=visible.is_overdue,
                    routine_title=visible.routine.title,
                    occurrence_role=visible.role.value,
                )
            )

    appointments = list(
        session.scalars(
            select(Appointment).where(
                Appointment.owner_id == owner_id,
                Appointment.status == AppointmentStatus.SCHEDULED.value,
            )
        )
    )
    for appointment in appointments:
        if not appointment_overlaps_day(
            is_all_day=appointment.is_all_day,
            start_date=appointment.start_date,
            end_date=appointment.end_date,
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            day=reference_date,
            timezone_name=policies.timezone,
        ):
            continue
        starts_at, ends_at = appointment_times_iso(
            is_all_day=appointment.is_all_day,
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
        )
        span_start = LocalDate.from_date(appointment.start_date)
        span_end = LocalDate.from_date(appointment.end_date)
        from planforge.domain.appointment_scheduling import span_segment_for_day

        segment = span_segment_for_day(
            reference_date,
            start_date=span_start,
            end_date=span_end,
        )
        items.append(
            TodayItem(
                kind=ViewItemKind.APPOINTMENT,
                item_id=appointment.id,
                title=appointment.title,
                notes=appointment.notes,
                due_date=reference_date,
                starts_at=starts_at,
                ends_at=ends_at,
                is_overdue=False,
                is_all_day=appointment.is_all_day,
                span_start_date=span_start,
                span_end_date=span_end,
                span_segment=segment.value,
                location=appointment.location,
                status=appointment.status,
            )
        )

    maintenance_items = list(
        session.scalars(
            select(MaintenanceDefinition).where(
                MaintenanceDefinition.owner_id == owner_id,
                MaintenanceDefinition.status == MaintenanceStatus.ACTIVE.value,
                MaintenanceDefinition.next_due_date.is_not(None),
            )
        )
    )
    lead_end = reference_date.add_days(policies.maintenance_lead_days).to_date()
    for maintenance in maintenance_items:
        assert maintenance.next_due_date is not None
        due = LocalDate.from_date(maintenance.next_due_date)
        if due.to_date() <= lead_end:
            items.append(
                TodayItem(
                    kind=ViewItemKind.MAINTENANCE,
                    item_id=maintenance.id,
                    title=maintenance.title,
                    notes=maintenance.notes,
                    due_date=due,
                    starts_at=None,
                    ends_at=None,
                    is_overdue=is_item_overdue(scheduled=due, today=reference_date),
                )
            )

    items.sort(
        key=lambda item: (
            2 if item.is_completed else 0 if item.is_overdue else 1,
            item.due_date.to_iso() if item.due_date else "",
            item.title.lower(),
        )
    )

    pending_ids = {(item.kind, item.item_id) for item in items}
    for completed in completed_items_for_local_day(
        session,
        owner_id=owner_id,
        day=reference_date,
        timezone_name=policies.timezone,
    ):
        key = (completed.kind, completed.item_id)
        if key in pending_ids:
            continue
        items.append(
            TodayItem(
                kind=completed.kind,
                item_id=completed.item_id,
                title=completed.title,
                notes=completed.notes,
                due_date=completed.due_date,
                starts_at=completed.starts_at,
                ends_at=completed.ends_at,
                is_overdue=False,
                routine_title=completed.routine_title,
                is_completed=True,
                is_all_day=completed.is_all_day,
                span_start_date=completed.span_start_date,
                span_end_date=completed.span_end_date,
                span_segment=completed.span_segment,
                location=completed.location,
                status=completed.status,
            )
        )

    items.sort(
        key=lambda item: (
            2 if item.is_completed else 0 if item.is_overdue else 1,
            item.due_date.to_iso() if item.due_date else "",
            item.title.lower(),
        )
    )
    return TodayView(reference_date=reference_date, items=items)
