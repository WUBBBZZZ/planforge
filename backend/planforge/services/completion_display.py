"""Helpers for showing completed planner items in views."""

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from planforge.domain.enums import CompletionAction, ViewItemKind
from planforge.domain.local_date import LocalDate
from planforge.domain.timezone import get_timezone
from planforge.models.appointment import Appointment
from planforge.models.completion_record import CompletionRecord
from planforge.models.maintenance import MaintenanceDefinition
from planforge.models.occurrence import Occurrence
from planforge.models.routine import Routine
from planforge.models.task import Task
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class CompletedViewItem:
    kind: ViewItemKind
    item_id: str
    title: str
    notes: str | None
    due_date: LocalDate | None
    starts_at: str | None
    ends_at: str | None
    is_overdue: bool
    routine_title: str | None = None
    is_completed: bool = True


def local_day_utc_bounds(
    day: LocalDate,
    *,
    timezone_name: str,
) -> tuple[datetime, datetime]:
    """Return UTC bounds for a local calendar day."""
    tz = get_timezone(timezone_name)
    start = datetime.combine(day.to_date(), time.min, tzinfo=tz)
    end = start + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def list_completed_records_for_local_day(
    session: Session,
    *,
    owner_id: str,
    day: LocalDate,
    timezone_name: str,
) -> list[CompletionRecord]:
    """Return completion records whose local recorded date matches day."""
    start_utc, end_utc = local_day_utc_bounds(day, timezone_name=timezone_name)
    return list(
        session.scalars(
            select(CompletionRecord)
            .where(
                CompletionRecord.owner_id == owner_id,
                CompletionRecord.action == CompletionAction.COMPLETED.value,
                CompletionRecord.recorded_at >= start_utc,
                CompletionRecord.recorded_at < end_utc,
            )
            .order_by(CompletionRecord.recorded_at)
        )
    )


def _task_item(task: Task) -> CompletedViewItem:
    due = LocalDate.from_date(task.due_date) if task.due_date else None
    return CompletedViewItem(
        kind=ViewItemKind.TASK,
        item_id=task.id,
        title=task.title,
        notes=task.notes,
        due_date=due,
        starts_at=None,
        ends_at=None,
        is_overdue=False,
    )


def _occurrence_item(occurrence: Occurrence, routine: Routine) -> CompletedViewItem:
    scheduled = LocalDate.from_date(occurrence.scheduled_date)
    return CompletedViewItem(
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


def _appointment_item(appointment: Appointment) -> CompletedViewItem:
    return CompletedViewItem(
        kind=ViewItemKind.APPOINTMENT,
        item_id=appointment.id,
        title=appointment.title,
        notes=appointment.notes,
        due_date=None,
        starts_at=appointment.starts_at.astimezone(UTC).isoformat(),
        ends_at=appointment.ends_at.astimezone(UTC).isoformat(),
        is_overdue=False,
    )


def _maintenance_item(
    maintenance: MaintenanceDefinition,
    *,
    completed_on: LocalDate,
) -> CompletedViewItem:
    return CompletedViewItem(
        kind=ViewItemKind.MAINTENANCE,
        item_id=maintenance.id,
        title=maintenance.title,
        notes=maintenance.notes,
        due_date=completed_on,
        starts_at=None,
        ends_at=None,
        is_overdue=False,
    )


def completed_items_for_local_day(
    session: Session,
    *,
    owner_id: str,
    day: LocalDate,
    timezone_name: str,
) -> list[CompletedViewItem]:
    """Build planner items completed on a local calendar day."""
    records = list_completed_records_for_local_day(
        session,
        owner_id=owner_id,
        day=day,
        timezone_name=timezone_name,
    )
    items: list[CompletedViewItem] = []
    seen: set[tuple[str, str]] = set()

    for record in records:
        key = (record.entity_type, record.entity_id)
        if key in seen:
            continue
        seen.add(key)

        if record.entity_type == "task":
            task = session.get(Task, record.entity_id)
            if task is None or task.owner_id != owner_id:
                continue
            items.append(_task_item(task))
            continue

        if record.entity_type == "occurrence":
            row = session.execute(
                select(Occurrence, Routine)
                .join(Routine, Routine.id == Occurrence.routine_id)
                .where(
                    Occurrence.id == record.entity_id,
                    Occurrence.owner_id == owner_id,
                )
            ).first()
            if row is None:
                continue
            occurrence, routine = row
            items.append(_occurrence_item(occurrence, routine))
            continue

        if record.entity_type == "appointment":
            appointment = session.get(Appointment, record.entity_id)
            if appointment is None or appointment.owner_id != owner_id:
                continue
            items.append(_appointment_item(appointment))
            continue

        if record.entity_type == "maintenance":
            maintenance = session.get(MaintenanceDefinition, record.entity_id)
            if maintenance is None or maintenance.owner_id != owner_id:
                continue
            items.append(
                _maintenance_item(maintenance, completed_on=day),
            )

    items.sort(key=lambda item: item.title.lower())
    return items
