"""Today view assembly."""

from dataclasses import dataclass
from datetime import UTC

from planforge.domain.enums import (
    AppointmentStatus,
    MaintenanceStatus,
    TaskStatus,
    ViewItemKind,
)
from planforge.domain.local_date import LocalDate
from planforge.domain.timezone import get_timezone
from planforge.models.appointment import Appointment
from planforge.models.maintenance import MaintenanceDefinition
from planforge.models.task import Task
from planforge.services import routine_service
from planforge.services.completion_display import completed_items_for_local_day
from planforge.services.display_date import is_item_overdue
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


@dataclass(frozen=True)
class TodayView:
    reference_date: LocalDate
    items: list[TodayItem]


def _appointment_local_date(
    appointment: Appointment,
    *,
    timezone_name: str,
) -> LocalDate:
    local = appointment.starts_at.astimezone(get_timezone(timezone_name))
    return LocalDate(local.year, local.month, local.day)


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
        routine_service.ensure_occurrences(
            session,
            owner_id=owner_id,
            clock_today=clock_today,
            policies=policies,
        )
        for occurrence, routine in routine_service.list_pending_occurrences(
            session,
            owner_id=owner_id,
        ):
            scheduled = LocalDate.from_date(occurrence.scheduled_date)
            if scheduled.to_date() == ref:
                items.append(
                    TodayItem(
                        kind=ViewItemKind.OCCURRENCE,
                        item_id=occurrence.id,
                        title=routine.title,
                        notes=routine.notes,
                        due_date=scheduled,
                        starts_at=None,
                        ends_at=None,
                        is_overdue=False,
                        routine_title=routine.title,
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
        local_date = _appointment_local_date(
            appointment,
            timezone_name=policies.timezone,
        )
        if local_date.to_date() == ref:
            items.append(
                TodayItem(
                    kind=ViewItemKind.APPOINTMENT,
                    item_id=appointment.id,
                    title=appointment.title,
                    notes=appointment.notes,
                    due_date=local_date,
                    starts_at=appointment.starts_at.astimezone(UTC).isoformat(),
                    ends_at=appointment.ends_at.astimezone(UTC).isoformat(),
                    is_overdue=False,
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
