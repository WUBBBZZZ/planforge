"""Maintenance business logic."""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Any

from planforge.core.exceptions import (
    AppointmentNotFoundError,
    MaintenanceLinkError,
    MaintenanceNotEditableError,
    MaintenanceNotFoundError,
    MaintenanceStateError,
    ValidationError,
)
from planforge.domain.enums import (
    AppointmentStatus,
    CompletionAction,
    MaintenanceIntervalUnit,
    MaintenanceListFilter,
    MaintenanceNextActionStatus,
    MaintenanceStatus,
)
from planforge.domain.local_date import LocalDate
from planforge.domain.maintenance_interval import compute_next_due_date
from planforge.models.appointment import Appointment
from planforge.models.completion_record import CompletionRecord
from planforge.models.maintenance import MaintenanceDefinition
from planforge.models.maintenance_completion import MaintenanceCompletion
from planforge.services import appointment_service
from planforge.services.display_date import is_item_overdue
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

_UNSET: Any = object()
UNSET = _UNSET


def _get_maintenance_or_raise(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceDefinition:
    item = session.scalar(
        select(MaintenanceDefinition).where(
            MaintenanceDefinition.id == maintenance_id,
            MaintenanceDefinition.owner_id == owner_id,
        )
    )
    if item is None:
        raise MaintenanceNotFoundError(f"Maintenance item not found: {maintenance_id}")
    return item


def _get_completion_or_raise(
    session: Session,
    *,
    completion_id: str,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceCompletion:
    completion = session.scalar(
        select(MaintenanceCompletion).where(
            MaintenanceCompletion.id == completion_id,
            MaintenanceCompletion.maintenance_definition_id == maintenance_id,
            MaintenanceCompletion.owner_id == owner_id,
        )
    )
    if completion is None:
        raise MaintenanceNotFoundError(
            f"Maintenance completion not found: {completion_id}"
        )
    return completion


def _append_audit(
    session: Session,
    *,
    owner_id: str,
    maintenance_id: str,
    action: CompletionAction,
) -> None:
    session.add(
        CompletionRecord(
            owner_id=owner_id,
            entity_type="maintenance",
            entity_id=maintenance_id,
            action=action.value,
            recorded_at=datetime.now(UTC),
        )
    )


def _validate_interval(
    *,
    interval_unit: MaintenanceIntervalUnit,
    interval_value: int | None,
) -> None:
    if interval_unit is MaintenanceIntervalUnit.MANUAL:
        return
    if interval_value is None or interval_value < 1:
        raise ValidationError("Interval value must be at least 1")


def _default_next_action(
    *,
    interval_unit: MaintenanceIntervalUnit,
    has_completion: bool,
) -> MaintenanceNextActionStatus:
    if interval_unit is MaintenanceIntervalUnit.MANUAL:
        return MaintenanceNextActionStatus.NO_NEXT_DATE
    if has_completion:
        return MaintenanceNextActionStatus.NEEDS_SCHEDULING
    return MaintenanceNextActionStatus.NO_NEXT_DATE


def resolve_maintenance_completion_date(
    item: MaintenanceDefinition,
    *,
    completed_on: LocalDate | None,
    clock_today: LocalDate,
) -> LocalDate:
    """Return the completion date to record for a maintenance item.

    Overdue work is recorded on the day it is marked complete, not back-dated
    to the original due date.
    """
    when = completed_on or clock_today
    if item.next_due_date is None:
        return when
    due = LocalDate.from_date(item.next_due_date)
    if is_item_overdue(scheduled=due, today=clock_today) and when <= due:
        return clock_today
    return when


def _reset_scheduling_state_after_due_change(item: MaintenanceDefinition) -> None:
    """Clear booked-forward state when derived due dates change."""
    item.linked_appointment_id = None
    item.scheduling_reminder_date = None
    if item.interval is MaintenanceIntervalUnit.MANUAL:
        item.next_action_status = MaintenanceNextActionStatus.NO_NEXT_DATE.value
    elif item.next_due_date is None:
        item.next_action_status = MaintenanceNextActionStatus.NO_NEXT_DATE.value
    else:
        item.next_action_status = MaintenanceNextActionStatus.NEEDS_SCHEDULING.value


def _sync_last_completed_from_history(
    session: Session,
    *,
    item: MaintenanceDefinition,
    force_scheduling_reset: bool = False,
) -> None:
    previous_last = item.last_completed_date
    previous_next_due = item.next_due_date

    latest = session.scalar(
        select(MaintenanceCompletion)
        .where(
            MaintenanceCompletion.maintenance_definition_id == item.id,
            MaintenanceCompletion.is_voided.is_(False),
        )
        .order_by(
            MaintenanceCompletion.completed_on.desc(),
            MaintenanceCompletion.created_at.desc(),
        )
        .limit(1)
    )
    if latest is None:
        item.last_completed_date = None
        item.next_due_date = None
        if item.interval is MaintenanceIntervalUnit.MANUAL:
            item.next_action_status = MaintenanceNextActionStatus.NO_NEXT_DATE.value
        else:
            item.next_action_status = _default_next_action(
                interval_unit=item.interval,
                has_completion=False,
            ).value
    else:
        completed = LocalDate.from_date(latest.completed_on)
        item.last_completed_date = latest.completed_on
        next_due = compute_next_due_date(
            completed,
            unit=item.interval,
            value=item.interval_value,
        )
        item.next_due_date = next_due.to_date() if next_due is not None else None

    dates_changed = (
        item.last_completed_date != previous_last
        or item.next_due_date != previous_next_due
    )
    if force_scheduling_reset or dates_changed:
        _reset_scheduling_state_after_due_change(item)


def list_completions(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    limit: int | None = None,
) -> list[MaintenanceCompletion]:
    query = (
        select(MaintenanceCompletion)
        .where(
            MaintenanceCompletion.maintenance_definition_id == maintenance_id,
            MaintenanceCompletion.owner_id == owner_id,
            MaintenanceCompletion.is_voided.is_(False),
        )
        .order_by(
            MaintenanceCompletion.completed_on.desc(),
            MaintenanceCompletion.created_at.desc(),
        )
    )
    if limit is not None:
        query = query.limit(limit)
    return list(session.scalars(query))


def create_maintenance(
    session: Session,
    *,
    owner_id: str,
    title: str,
    category: str | None = None,
    notes: str | None = None,
    interval_unit: MaintenanceIntervalUnit = MaintenanceIntervalUnit.MONTHS,
    interval_value: int | None = 6,
    lead_time_days: int = 30,
    reminder_offset_days: int | None = None,
) -> MaintenanceDefinition:
    """Create an active maintenance definition."""
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValidationError("Title must not be empty")
    _validate_interval(interval_unit=interval_unit, interval_value=interval_value)
    if lead_time_days < 0:
        raise ValidationError("Lead time must be zero or positive")

    item = MaintenanceDefinition(
        owner_id=owner_id,
        title=cleaned_title,
        category=category,
        notes=notes,
        interval_unit=interval_unit.value,
        interval_value=interval_value,
        lead_time_days=lead_time_days,
        reminder_offset_days=reminder_offset_days,
        status=MaintenanceStatus.ACTIVE.value,
        next_action_status=_default_next_action(
            interval_unit=interval_unit,
            has_completion=False,
        ).value,
    )
    session.add(item)
    session.flush()
    return item


def get_maintenance(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceDefinition:
    return _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )


def list_maintenance(
    session: Session,
    *,
    owner_id: str,
    list_filter: MaintenanceListFilter | None = None,
    status: MaintenanceStatus | None = None,
    today: LocalDate | None = None,
) -> list[MaintenanceDefinition]:
    query = select(MaintenanceDefinition).where(
        MaintenanceDefinition.owner_id == owner_id
    )
    if status is not None:
        query = query.where(MaintenanceDefinition.status == status.value)
    elif list_filter is not None and today is not None:
        query = _apply_list_filter(query, list_filter=list_filter, today=today)
    query = query.order_by(MaintenanceDefinition.title)
    items = list(session.scalars(query))
    if list_filter is MaintenanceListFilter.DUE_SOON and today is not None:
        return _filter_due_soon(items, today=today)
    return items


def _apply_list_filter(
    query: Select[tuple[MaintenanceDefinition]],
    *,
    list_filter: MaintenanceListFilter,
    today: LocalDate,
) -> Select[tuple[MaintenanceDefinition]]:
    today_date = today.to_date()
    if list_filter is MaintenanceListFilter.ARCHIVED:
        return query.where(
            MaintenanceDefinition.status == MaintenanceStatus.ARCHIVED.value
        )
    query = query.where(MaintenanceDefinition.status == MaintenanceStatus.ACTIVE.value)
    if list_filter is MaintenanceListFilter.ACTIVE:
        return query
    if list_filter is MaintenanceListFilter.NEEDS_SCHEDULING:
        return query.where(
            MaintenanceDefinition.next_action_status
            == MaintenanceNextActionStatus.NEEDS_SCHEDULING.value
        )
    if list_filter is MaintenanceListFilter.SCHEDULED_UPCOMING:
        return query.where(
            MaintenanceDefinition.next_action_status
            == MaintenanceNextActionStatus.SCHEDULED.value,
            MaintenanceDefinition.linked_appointment_id.is_not(None),
        )
    if list_filter is MaintenanceListFilter.OVERDUE:
        return query.where(
            MaintenanceDefinition.next_due_date.is_not(None),
            MaintenanceDefinition.next_due_date < today_date,
        )
    if list_filter is MaintenanceListFilter.DUE_SOON:
        return query.where(MaintenanceDefinition.next_due_date.is_not(None))
    return query


def _filter_due_soon(
    items: list[MaintenanceDefinition],
    *,
    today: LocalDate,
) -> list[MaintenanceDefinition]:
    return [
        item
        for item in items
        if item.next_due_date is not None
        and today.to_date()
        <= item.next_due_date
        <= today.add_days(item.lead_time_days).to_date()
    ]


def update_maintenance(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    title: str | None | Any = _UNSET,
    category: str | None | Any = _UNSET,
    notes: str | None | Any = _UNSET,
    interval_unit: MaintenanceIntervalUnit | None | Any = _UNSET,
    interval_value: int | None | Any = _UNSET,
    lead_time_days: int | None | Any = _UNSET,
    reminder_offset_days: int | None | Any = _UNSET,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ACTIVE:
        raise MaintenanceNotEditableError("Only active maintenance can be edited")

    if title is not _UNSET:
        cleaned = title.strip() if title is not None else ""
        if not cleaned:
            raise ValidationError("Title must not be empty")
        item.title = cleaned
    if category is not _UNSET:
        item.category = category
    if notes is not _UNSET:
        item.notes = notes
    if interval_unit is not _UNSET:
        assert isinstance(interval_unit, MaintenanceIntervalUnit)
        item.interval_unit = interval_unit.value
    if interval_value is not _UNSET:
        item.interval_value = interval_value
    if lead_time_days is not _UNSET:
        if lead_time_days is not None and lead_time_days < 0:
            raise ValidationError("Lead time must be zero or positive")
        item.lead_time_days = lead_time_days if lead_time_days is not None else 30
    if reminder_offset_days is not _UNSET:
        item.reminder_offset_days = reminder_offset_days

    _validate_interval(interval_unit=item.interval, interval_value=item.interval_value)
    _sync_last_completed_from_history(session, item=item)
    session.flush()
    return item


def archive_maintenance(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is MaintenanceStatus.ARCHIVED:
        raise MaintenanceStateError("Maintenance is already archived")
    item.status = MaintenanceStatus.ARCHIVED.value
    item.next_action_status = MaintenanceNextActionStatus.NOT_APPLICABLE.value
    _append_audit(
        session,
        owner_id=owner_id,
        maintenance_id=item.id,
        action=CompletionAction.ARCHIVED,
    )
    session.flush()
    return item


def restore_maintenance(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ARCHIVED:
        raise MaintenanceStateError("Only archived maintenance can be restored")
    item.status = MaintenanceStatus.ACTIVE.value
    if item.linked_appointment_id:
        item.next_action_status = MaintenanceNextActionStatus.SCHEDULED.value
    elif item.scheduling_reminder_date:
        item.next_action_status = MaintenanceNextActionStatus.REMINDER_SET.value
    elif item.last_completed_date:
        item.next_action_status = MaintenanceNextActionStatus.NEEDS_SCHEDULING.value
    else:
        item.next_action_status = _default_next_action(
            interval_unit=item.interval,
            has_completion=False,
        ).value
    _append_audit(
        session,
        owner_id=owner_id,
        maintenance_id=item.id,
        action=CompletionAction.RESTORED,
    )
    session.flush()
    return item


def _record_completion(
    session: Session,
    *,
    owner_id: str,
    item: MaintenanceDefinition,
    completed_on: LocalDate,
    notes: str | None,
) -> MaintenanceCompletion:
    completion = MaintenanceCompletion(
        owner_id=owner_id,
        maintenance_definition_id=item.id,
        completed_on=completed_on.to_date(),
        notes=notes,
    )
    session.add(completion)
    session.flush()
    _sync_last_completed_from_history(
        session,
        item=item,
        force_scheduling_reset=True,
    )
    return completion


def complete_maintenance(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    completed_on: LocalDate | None = None,
    clock_today: LocalDate | None = None,
    notes: str | None = None,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ACTIVE:
        raise MaintenanceStateError("Only active maintenance can be completed")
    today = clock_today or LocalDate.from_date(datetime.now(UTC).date())
    when = resolve_maintenance_completion_date(
        item,
        completed_on=completed_on,
        clock_today=today,
    )
    _record_completion(
        session,
        owner_id=owner_id,
        item=item,
        completed_on=when,
        notes=notes,
    )
    _append_audit(
        session,
        owner_id=owner_id,
        maintenance_id=item.id,
        action=CompletionAction.COMPLETED,
    )
    session.flush()
    return item


def add_historical_completion(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    completed_on: LocalDate,
    notes: str | None = None,
) -> MaintenanceCompletion:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ACTIVE:
        raise MaintenanceStateError("Only active maintenance accepts history")
    completion = MaintenanceCompletion(
        owner_id=owner_id,
        maintenance_definition_id=item.id,
        completed_on=completed_on.to_date(),
        notes=notes,
    )
    session.add(completion)
    session.flush()
    _sync_last_completed_from_history(session, item=item)
    session.flush()
    return completion


def correct_completion(
    session: Session,
    *,
    maintenance_id: str,
    completion_id: str,
    owner_id: str,
    completed_on: LocalDate,
    notes: str | None = None,
    void_reason: str | None = None,
) -> MaintenanceCompletion:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    original = _get_completion_or_raise(
        session,
        completion_id=completion_id,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if original.is_voided:
        raise MaintenanceStateError("Completion has already been voided")

    original.is_voided = True
    original.voided_at = datetime.now(UTC)
    original.void_reason = void_reason

    replacement = MaintenanceCompletion(
        owner_id=owner_id,
        maintenance_definition_id=item.id,
        completed_on=completed_on.to_date(),
        notes=notes,
    )
    session.add(replacement)
    session.flush()
    original.superseded_by_id = replacement.id
    _sync_last_completed_from_history(session, item=item)
    session.flush()
    return replacement


def _ensure_no_duplicate_link(
    session: Session,
    *,
    owner_id: str,
    maintenance_id: str,
    appointment_id: str,
) -> None:
    existing = session.scalar(
        select(MaintenanceDefinition).where(
            MaintenanceDefinition.owner_id == owner_id,
            MaintenanceDefinition.linked_appointment_id == appointment_id,
            MaintenanceDefinition.id != maintenance_id,
        )
    )
    if existing is not None:
        raise MaintenanceLinkError(
            "Appointment is already linked to another maintenance item"
        )


def _link_appointment(
    session: Session,
    *,
    item: MaintenanceDefinition,
    appointment: Appointment,
    owner_id: str,
) -> None:
    if appointment.appointment_status is not AppointmentStatus.SCHEDULED:
        raise MaintenanceLinkError("Only scheduled appointments can be linked")
    _ensure_no_duplicate_link(
        session,
        owner_id=owner_id,
        maintenance_id=item.id,
        appointment_id=appointment.id,
    )
    if item.linked_appointment_id and item.linked_appointment_id != appointment.id:
        raise MaintenanceLinkError("Maintenance already has a linked appointment")
    appointment.maintenance_definition_id = item.id
    item.linked_appointment_id = appointment.id
    item.next_action_status = MaintenanceNextActionStatus.SCHEDULED.value
    item.scheduling_reminder_date = None


def link_appointment(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    appointment_id: str,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ACTIVE:
        raise MaintenanceStateError("Only active maintenance can link appointments")
    appointment = session.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.owner_id == owner_id,
        )
    )
    if appointment is None:
        raise AppointmentNotFoundError(f"Appointment not found: {appointment_id}")
    _link_appointment(session, item=item, appointment=appointment, owner_id=owner_id)
    session.flush()
    return item


def schedule_appointment(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    title: str | None,
    start_date: LocalDate,
    end_date: LocalDate,
    is_all_day: bool,
    start_time: time | None,
    end_time: time | None,
    timezone_name: str,
    location: str | None = None,
    notes: str | None = None,
) -> tuple[MaintenanceDefinition, Appointment]:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ACTIVE:
        raise MaintenanceStateError("Only active maintenance can schedule appointments")
    if item.linked_appointment_id:
        raise MaintenanceLinkError(
            "Maintenance already has a linked appointment; "
            "reschedule or cancel it first"
        )

    appointment = appointment_service.create_appointment(
        session,
        owner_id=owner_id,
        title=title or item.title,
        notes=notes,
        location=location,
        category=item.category,
        reminder_minutes=None,
        maintenance_definition_id=item.id,
        is_all_day=is_all_day,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        timezone_name=timezone_name,
    )
    _link_appointment(session, item=item, appointment=appointment, owner_id=owner_id)
    session.flush()
    return item, appointment


def reschedule_linked_appointment(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    is_all_day: bool,
    start_date: LocalDate,
    end_date: LocalDate,
    start_time: time | None,
    end_time: time | None,
    timezone_name: str,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.linked_appointment_id is None:
        raise MaintenanceLinkError(
            "Maintenance has no linked appointment to reschedule"
        )
    appointment_service.reschedule_appointment(
        session,
        appointment_id=item.linked_appointment_id,
        owner_id=owner_id,
        is_all_day=is_all_day,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        timezone_name=timezone_name,
    )
    session.flush()
    return item


def set_scheduling_reminder(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    reminder_date: LocalDate,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ACTIVE:
        raise MaintenanceStateError("Only active maintenance can set reminders")
    if item.linked_appointment_id:
        raise MaintenanceLinkError(
            "Cannot set a scheduling reminder while an appointment is linked"
        )
    item.scheduling_reminder_date = reminder_date.to_date()
    item.next_action_status = MaintenanceNextActionStatus.REMINDER_SET.value
    session.flush()
    return item


def clear_scheduling_reminder(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    item.scheduling_reminder_date = None
    if item.next_action_status == MaintenanceNextActionStatus.REMINDER_SET.value:
        if item.last_completed_date:
            item.next_action_status = MaintenanceNextActionStatus.NEEDS_SCHEDULING.value
        else:
            item.next_action_status = MaintenanceNextActionStatus.NO_NEXT_DATE.value
    session.flush()
    return item


def clear_next_action(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceDefinition:
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.linked_appointment_id:
        raise MaintenanceLinkError(
            "Cancel the linked appointment before clearing next action"
        )
    item.scheduling_reminder_date = None
    item.next_action_status = MaintenanceNextActionStatus.NO_NEXT_DATE.value
    session.flush()
    return item


def handle_linked_appointment_cancelled(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> None:
    """Return linked maintenance to needs_scheduling when appointment is cancelled."""
    item = session.scalar(
        select(MaintenanceDefinition).where(
            MaintenanceDefinition.owner_id == owner_id,
            MaintenanceDefinition.linked_appointment_id == appointment_id,
        )
    )
    if item is None:
        return
    item.linked_appointment_id = None
    item.next_action_status = MaintenanceNextActionStatus.NEEDS_SCHEDULING.value
    session.flush()


def build_history_board(
    session: Session,
    *,
    owner_id: str,
    today: LocalDate,
    history_limit: int = 10,
) -> list[dict[str, object]]:
    """Build rows for the horizontal maintenance history board."""
    items = list_maintenance(
        session,
        owner_id=owner_id,
        list_filter=MaintenanceListFilter.ACTIVE,
        today=today,
    )
    archived = list_maintenance(
        session,
        owner_id=owner_id,
        status=MaintenanceStatus.ARCHIVED,
        today=today,
    )
    rows: list[dict[str, object]] = []
    for item in [*items, *archived]:
        completions = list_completions(
            session,
            maintenance_id=item.id,
            owner_id=owner_id,
            limit=history_limit,
        )
        linked = None
        if item.linked_appointment_id:
            linked = session.get(Appointment, item.linked_appointment_id)
        rows.append(
            {
                "maintenance": item,
                "completions": completions,
                "linked_appointment": linked,
            }
        )
    return rows
