"""Appointment business logic."""

from datetime import UTC, datetime

from planforge.core.exceptions import (
    AppointmentNotFoundError,
    AppointmentStateError,
    ValidationError,
)
from planforge.domain.enums import AppointmentStatus, CompletionAction
from planforge.models.appointment import Appointment
from planforge.models.completion_record import CompletionRecord
from sqlalchemy import select
from sqlalchemy.orm import Session


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


def create_appointment(
    session: Session,
    *,
    owner_id: str,
    title: str,
    notes: str | None,
    starts_at: datetime,
    ends_at: datetime,
) -> Appointment:
    """Create a scheduled appointment."""
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValidationError("Title must not be empty")
    if ends_at <= starts_at:
        raise ValidationError("End time must be after start time")

    appointment = Appointment(
        owner_id=owner_id,
        title=cleaned_title,
        notes=notes,
        starts_at=starts_at.astimezone(UTC),
        ends_at=ends_at.astimezone(UTC),
        status=AppointmentStatus.SCHEDULED.value,
    )
    session.add(appointment)
    session.flush()
    return appointment


def list_appointments(
    session: Session,
    *,
    owner_id: str,
    status: AppointmentStatus | None = AppointmentStatus.SCHEDULED,
) -> list[Appointment]:
    """List appointments for an owner."""
    query = select(Appointment).where(Appointment.owner_id == owner_id)
    if status is not None:
        query = query.where(Appointment.status == status.value)
    query = query.order_by(Appointment.starts_at)
    return list(session.scalars(query))


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
    session.add(
        CompletionRecord(
            owner_id=owner_id,
            entity_type="appointment",
            entity_id=appointment.id,
            action=CompletionAction.COMPLETED.value,
            recorded_at=datetime.now(UTC),
        )
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
    session.add(
        CompletionRecord(
            owner_id=owner_id,
            entity_type="appointment",
            entity_id=appointment.id,
            action=CompletionAction.CANCELLED.value,
            recorded_at=datetime.now(UTC),
        )
    )
    session.flush()
    return appointment
