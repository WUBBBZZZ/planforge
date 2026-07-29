"""Pydantic schemas for appointments."""

from datetime import date, datetime, time

from planforge.domain.enums import AppointmentListFilter, AppointmentStatus
from planforge.models.appointment import Appointment
from pydantic import BaseModel, Field


class AppointmentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str | None = None
    location: str | None = None
    category: str | None = None
    reminder_minutes: int | None = Field(default=None, ge=0)
    maintenance_definition_id: str | None = None
    is_all_day: bool = False
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None


class AppointmentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    notes: str | None = None
    location: str | None = None
    category: str | None = None
    reminder_minutes: int | None = Field(default=None, ge=0)
    maintenance_definition_id: str | None = None


class AppointmentRescheduleRequest(BaseModel):
    is_all_day: bool
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None


class AppointmentResponse(BaseModel):
    id: str
    title: str
    notes: str | None
    location: str | None
    category: str | None
    reminder_minutes: int | None
    maintenance_definition_id: str | None
    is_all_day: bool
    start_date: date
    end_date: date
    starts_at: datetime | None
    ends_at: datetime | None
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_appointment(cls, appointment: Appointment) -> AppointmentResponse:
        return cls(
            id=appointment.id,
            title=appointment.title,
            notes=appointment.notes,
            location=appointment.location,
            category=appointment.category,
            reminder_minutes=appointment.reminder_minutes,
            maintenance_definition_id=appointment.maintenance_definition_id,
            is_all_day=appointment.is_all_day,
            start_date=appointment.start_date,
            end_date=appointment.end_date,
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            status=appointment.appointment_status,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
        )


class AppointmentListQuery(BaseModel):
    list_filter: AppointmentListFilter | None = None
    status: AppointmentStatus | None = None
    search: str | None = None
