"""Appointment business logic."""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Any

from planforge.core.exceptions import (
    AppointmentDeleteError,
    AppointmentNotEditableError,
    AppointmentNotFoundError,
    AppointmentStateError,
    MaintenanceNotFoundError,
    ValidationError,
)
from planforge.domain.appointment_scheduling import (
    AppointmentScheduleInput,
    build_schedule_input,
    combine_local_datetime,
    local_date_from_instant,
)
from planforge.domain.enums import (
    AppointmentListFilter,
    AppointmentStatus,
    CompletionAction,
)
from planforge.domain.local_date import LocalDate
from planforge.models.appointment import Appointment
from planforge.models.completion_record import CompletionRecord
from planforge.models.maintenance import MaintenanceDefinition
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

_UNSET: Any = object()
UNSET = _UNSET


def _get_appointment_or_raise(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> Appointment:
    appointment = session.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.owner_id == owner_id,
        )
    )
    if appointment is None:
        raise AppointmentNotFoundError(f"Appointment not found: {appointment_id}")
    return appointment


def _append_completion_record(
    session: Session,
    *,
    owner_id: str,
    appointment_id: str,
    action: CompletionAction,
) -> None:
    session.add(
        CompletionRecord(
            owner_id=owner_id,
            entity_type="appointment",
            entity_id=appointment_id,
            action=action.value,
            recorded_at=datetime.now(UTC),
        )
    )


def _validate_maintenance_link(
    session: Session,
    *,
    owner_id: str,
    maintenance_definition_id: str | None,
) -> None:
    if maintenance_definition_id is None:
        return
    maintenance = session.scalar(
        select(MaintenanceDefinition).where(
            MaintenanceDefinition.id == maintenance_definition_id,
            MaintenanceDefinition.owner_id == owner_id,
        )
    )
    if maintenance is None:
        raise MaintenanceNotFoundError(
            f"Maintenance definition not found: {maintenance_definition_id}"
        )


def _apply_schedule(
    appointment: Appointment,
    schedule: AppointmentScheduleInput,
) -> None:
    appointment.is_all_day = schedule.is_all_day
    appointment.start_date = schedule.start_date.to_date()
    appointment.end_date = schedule.end_date.to_date()
    appointment.starts_at = schedule.starts_at
    appointment.ends_at = schedule.ends_at


def _build_timed_instants(
    *,
    start_date: LocalDate,
    end_date: LocalDate,
    start_time: time | None,
    end_time: time | None,
    timezone_name: str,
) -> tuple[datetime, datetime]:
    if start_time is None or end_time is None:
        raise ValidationError("Timed appointments require start and end times")
    starts_at = combine_local_datetime(
        start_date,
        start_time,
        timezone_name=timezone_name,
    )
    ends_at = combine_local_datetime(end_date, end_time, timezone_name=timezone_name)
    return starts_at, ends_at


def create_appointment(
    session: Session,
    *,
    owner_id: str,
    title: str,
    notes: str | None,
    location: str | None,
    category: str | None,
    reminder_minutes: int | None,
    maintenance_definition_id: str | None,
    is_all_day: bool,
    start_date: LocalDate,
    end_date: LocalDate,
    start_time: time | None,
    end_time: time | None,
    timezone_name: str,
) -> Appointment:
    """Create a scheduled appointment."""
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValidationError("Title must not be empty")
    _validate_maintenance_link(
        session,
        owner_id=owner_id,
        maintenance_definition_id=maintenance_definition_id,
    )

    starts_at: datetime | None = None
    ends_at: datetime | None = None
    if not is_all_day:
        starts_at, ends_at = _build_timed_instants(
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            timezone_name=timezone_name,
        )

    schedule = build_schedule_input(
        is_all_day=is_all_day,
        start_date=start_date,
        end_date=end_date,
        starts_at=starts_at,
        ends_at=ends_at,
        timezone_name=timezone_name,
    )

    appointment = Appointment(
        owner_id=owner_id,
        title=cleaned_title,
        notes=notes,
        location=location,
        category=category,
        reminder_minutes=reminder_minutes,
        maintenance_definition_id=maintenance_definition_id,
        status=AppointmentStatus.SCHEDULED.value,
    )
    _apply_schedule(appointment, schedule)
    session.add(appointment)
    session.flush()
    return appointment


def get_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> Appointment:
    """Return a single appointment."""
    return _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )


def list_appointments(
    session: Session,
    *,
    owner_id: str,
    list_filter: AppointmentListFilter | None = None,
    status: AppointmentStatus | None = None,
    search: str | None = None,
    today: LocalDate | None = None,
) -> list[Appointment]:
    """List appointments for an owner with optional filters."""
    query = select(Appointment).where(Appointment.owner_id == owner_id)

    if status is not None:
        query = query.where(Appointment.status == status.value)
    elif list_filter is not None and today is not None:
        query = _apply_list_filter(query, list_filter=list_filter, today=today)

    if search:
        term = f"%{search.strip().lower()}%"
        query = query.where(
            Appointment.title.ilike(term)
            | Appointment.notes.ilike(term)
            | Appointment.location.ilike(term)
            | Appointment.category.ilike(term)
        )

    query = query.order_by(
        Appointment.start_date, Appointment.starts_at, Appointment.title
    )
    return list(session.scalars(query))


def _apply_list_filter(
    query: Select[tuple[Appointment]],
    *,
    list_filter: AppointmentListFilter,
    today: LocalDate,
) -> Select[tuple[Appointment]]:
    today_date = today.to_date()
    if list_filter is AppointmentListFilter.CANCELLED:
        return query.where(Appointment.status == AppointmentStatus.CANCELLED.value)
    if list_filter is AppointmentListFilter.ARCHIVED:
        return query.where(Appointment.status == AppointmentStatus.ARCHIVED.value)
    if list_filter is AppointmentListFilter.COMPLETED:
        return query.where(Appointment.status == AppointmentStatus.COMPLETED.value)
    if list_filter is AppointmentListFilter.SCHEDULED:
        return query.where(Appointment.status == AppointmentStatus.SCHEDULED.value)
    if list_filter is AppointmentListFilter.TODAY:
        return query.where(
            Appointment.status == AppointmentStatus.SCHEDULED.value,
            Appointment.start_date <= today_date,
            Appointment.end_date >= today_date,
        )
    if list_filter is AppointmentListFilter.UPCOMING:
        return query.where(
            Appointment.status == AppointmentStatus.SCHEDULED.value,
            Appointment.end_date >= today_date,
        )
    if list_filter is AppointmentListFilter.PAST:
        return query.where(
            Appointment.status.in_(
                [
                    AppointmentStatus.SCHEDULED.value,
                    AppointmentStatus.COMPLETED.value,
                ]
            ),
            Appointment.end_date < today_date,
        )
    return query


def update_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
    title: str | None | Any = _UNSET,
    notes: str | None | Any = _UNSET,
    location: str | None | Any = _UNSET,
    category: str | None | Any = _UNSET,
    reminder_minutes: int | None | Any = _UNSET,
    maintenance_definition_id: str | None | Any = _UNSET,
) -> Appointment:
    """Update editable fields on a scheduled appointment."""
    appointment = _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )
    if appointment.appointment_status is not AppointmentStatus.SCHEDULED:
        raise AppointmentNotEditableError("Only scheduled appointments can be edited")

    if title is not _UNSET:
        cleaned_title = title.strip() if title is not None else ""
        if not cleaned_title:
            raise ValidationError("Title must not be empty")
        appointment.title = cleaned_title
    if notes is not _UNSET:
        appointment.notes = notes
    if location is not _UNSET:
        appointment.location = location
    if category is not _UNSET:
        appointment.category = category
    if reminder_minutes is not _UNSET:
        appointment.reminder_minutes = reminder_minutes
    if maintenance_definition_id is not _UNSET:
        _validate_maintenance_link(
            session,
            owner_id=owner_id,
            maintenance_definition_id=maintenance_definition_id,
        )
        appointment.maintenance_definition_id = maintenance_definition_id

    session.flush()
    return appointment


def reschedule_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
    is_all_day: bool,
    start_date: LocalDate,
    end_date: LocalDate,
    start_time: time | None,
    end_time: time | None,
    timezone_name: str,
) -> Appointment:
    """Reschedule a scheduled appointment."""
    appointment = _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )
    if appointment.appointment_status is not AppointmentStatus.SCHEDULED:
        raise AppointmentNotEditableError(
            "Only scheduled appointments can be rescheduled"
        )

    starts_at: datetime | None = None
    ends_at: datetime | None = None
    if not is_all_day:
        starts_at, ends_at = _build_timed_instants(
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            timezone_name=timezone_name,
        )

    schedule = build_schedule_input(
        is_all_day=is_all_day,
        start_date=start_date,
        end_date=end_date,
        starts_at=starts_at,
        ends_at=ends_at,
        timezone_name=timezone_name,
    )
    _apply_schedule(appointment, schedule)
    session.flush()
    return appointment


def complete_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> Appointment:
    """Mark an appointment completed."""
    appointment = _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )
    if appointment.appointment_status is not AppointmentStatus.SCHEDULED:
        raise AppointmentStateError("Only scheduled appointments can be completed")
    appointment.status = AppointmentStatus.COMPLETED.value
    _append_completion_record(
        session,
        owner_id=owner_id,
        appointment_id=appointment.id,
        action=CompletionAction.COMPLETED,
    )
    session.flush()
    return appointment


def cancel_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> Appointment:
    """Cancel a scheduled appointment."""
    appointment = _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )
    if appointment.appointment_status is not AppointmentStatus.SCHEDULED:
        raise AppointmentStateError("Only scheduled appointments can be cancelled")
    appointment.status = AppointmentStatus.CANCELLED.value
    _append_completion_record(
        session,
        owner_id=owner_id,
        appointment_id=appointment.id,
        action=CompletionAction.CANCELLED,
    )
    from planforge.services import maintenance_service

    maintenance_service.handle_linked_appointment_cancelled(
        session,
        appointment_id=appointment.id,
        owner_id=owner_id,
    )
    session.flush()
    return appointment


def reopen_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> Appointment:
    """Restore a cancelled appointment to scheduled."""
    appointment = _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )
    if appointment.appointment_status is not AppointmentStatus.CANCELLED:
        raise AppointmentStateError("Only cancelled appointments can be reopened")
    appointment.status = AppointmentStatus.SCHEDULED.value
    _append_completion_record(
        session,
        owner_id=owner_id,
        appointment_id=appointment.id,
        action=CompletionAction.REOPENED,
    )
    session.flush()
    return appointment


def archive_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> Appointment:
    """Archive a scheduled appointment."""
    appointment = _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )
    if appointment.appointment_status is not AppointmentStatus.SCHEDULED:
        raise AppointmentStateError("Only scheduled appointments can be archived")
    appointment.status = AppointmentStatus.ARCHIVED.value
    _append_completion_record(
        session,
        owner_id=owner_id,
        appointment_id=appointment.id,
        action=CompletionAction.ARCHIVED,
    )
    session.flush()
    return appointment


def restore_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> Appointment:
    """Restore an archived appointment to scheduled."""
    appointment = _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )
    if appointment.appointment_status is not AppointmentStatus.ARCHIVED:
        raise AppointmentStateError("Only archived appointments can be restored")
    appointment.status = AppointmentStatus.SCHEDULED.value
    _append_completion_record(
        session,
        owner_id=owner_id,
        appointment_id=appointment.id,
        action=CompletionAction.RESTORED,
    )
    session.flush()
    return appointment


def delete_appointment(
    session: Session,
    *,
    appointment_id: str,
    owner_id: str,
) -> None:
    """Delete an appointment when no audit history exists."""
    appointment = _get_appointment_or_raise(
        session,
        appointment_id=appointment_id,
        owner_id=owner_id,
    )
    has_history = session.scalar(
        select(CompletionRecord.id)
        .where(
            CompletionRecord.owner_id == owner_id,
            CompletionRecord.entity_type == "appointment",
            CompletionRecord.entity_id == appointment_id,
        )
        .limit(1)
    )
    if has_history is not None:
        raise AppointmentDeleteError(
            "Appointments with completion history cannot be deleted"
        )
    session.delete(appointment)
    session.flush()


def appointment_end_local_date(
    appointment: Appointment,
    *,
    timezone_name: str,
) -> LocalDate:
    """Return the inclusive local end date for sorting and filters."""
    if appointment.is_all_day:
        return LocalDate.from_date(appointment.end_date)
    assert appointment.ends_at is not None
    return local_date_from_instant(appointment.ends_at, timezone_name=timezone_name)
