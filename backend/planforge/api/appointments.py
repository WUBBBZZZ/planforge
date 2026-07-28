"""Appointment API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import AppointmentStatus
from planforge.models.appointment import Appointment
from planforge.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str | None = None
    starts_at: datetime
    ends_at: datetime


class AppointmentResponse(BaseModel):
    id: str
    title: str
    notes: str | None
    starts_at: datetime
    ends_at: datetime
    status: AppointmentStatus

    @classmethod
    def from_appointment(cls, appointment: Appointment) -> AppointmentResponse:
        return cls(
            id=appointment.id,
            title=appointment.title,
            notes=appointment.notes,
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            status=appointment.appointment_status,
        )


@router.get("", response_model=list[AppointmentResponse])
def list_appointments_endpoint(
    session: Session = Depends(get_db),
) -> list[AppointmentResponse]:
    appointments = appointment_service.list_appointments(
        session,
        owner_id=LOCAL_OWNER_ID,
    )
    return [
        AppointmentResponse.from_appointment(appointment)
        for appointment in appointments
    ]


@router.post(
    "", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED
)
def create_appointment_endpoint(
    body: AppointmentCreateRequest,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = appointment_service.create_appointment(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
    )
    return AppointmentResponse.from_appointment(appointment)


@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
def complete_appointment_endpoint(
    appointment_id: str,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = appointment_service.complete_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return AppointmentResponse.from_appointment(appointment)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment_endpoint(
    appointment_id: str,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = appointment_service.cancel_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return AppointmentResponse.from_appointment(appointment)
