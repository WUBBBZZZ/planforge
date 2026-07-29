"""Appointment API endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import AppointmentListFilter, AppointmentStatus
from planforge.domain.local_date import LocalDate
from planforge.domain.planner_clock import PlannerClock
from planforge.schemas.appointment import (
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentResponse,
    AppointmentUpdateRequest,
)
from planforge.services import appointment_service
from planforge.services.appointment_service import UNSET
from planforge.services.settings_service import get_policy_snapshot

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("", response_model=list[AppointmentResponse])
def list_appointments_endpoint(
    session: Session = Depends(get_db),
    list_filter: AppointmentListFilter | None = Query(default=None, alias="filter"),
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1),
) -> list[AppointmentResponse]:
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    clock = PlannerClock(policies.timezone)
    appointments = appointment_service.list_appointments(
        session,
        owner_id=LOCAL_OWNER_ID,
        list_filter=list_filter,
        status=status_filter,
        search=search,
        today=clock.today(),
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
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    appointment = appointment_service.create_appointment(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
        location=body.location,
        category=body.category,
        reminder_minutes=body.reminder_minutes,
        maintenance_definition_id=body.maintenance_definition_id,
        is_all_day=body.is_all_day,
        start_date=LocalDate.from_date(body.start_date),
        end_date=LocalDate.from_date(body.end_date),
        start_time=body.start_time,
        end_time=body.end_time,
        timezone_name=policies.timezone,
    )
    return AppointmentResponse.from_appointment(appointment)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment_endpoint(
    appointment_id: str,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = appointment_service.get_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return AppointmentResponse.from_appointment(appointment)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment_endpoint(
    appointment_id: str,
    body: AppointmentUpdateRequest,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = appointment_service.update_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
        title=body.title if "title" in body.model_fields_set else UNSET,
        notes=body.notes if "notes" in body.model_fields_set else UNSET,
        location=body.location if "location" in body.model_fields_set else UNSET,
        category=body.category if "category" in body.model_fields_set else UNSET,
        reminder_minutes=(
            body.reminder_minutes
            if "reminder_minutes" in body.model_fields_set
            else UNSET
        ),
        maintenance_definition_id=(
            body.maintenance_definition_id
            if "maintenance_definition_id" in body.model_fields_set
            else UNSET
        ),
    )
    return AppointmentResponse.from_appointment(appointment)


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment_endpoint(
    appointment_id: str,
    body: AppointmentRescheduleRequest,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    appointment = appointment_service.reschedule_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
        is_all_day=body.is_all_day,
        start_date=LocalDate.from_date(body.start_date),
        end_date=LocalDate.from_date(body.end_date),
        start_time=body.start_time,
        end_time=body.end_time,
        timezone_name=policies.timezone,
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


@router.post("/{appointment_id}/reopen", response_model=AppointmentResponse)
def reopen_appointment_endpoint(
    appointment_id: str,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = appointment_service.reopen_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return AppointmentResponse.from_appointment(appointment)


@router.post("/{appointment_id}/archive", response_model=AppointmentResponse)
def archive_appointment_endpoint(
    appointment_id: str,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = appointment_service.archive_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return AppointmentResponse.from_appointment(appointment)


@router.post("/{appointment_id}/restore", response_model=AppointmentResponse)
def restore_appointment_endpoint(
    appointment_id: str,
    session: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = appointment_service.restore_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return AppointmentResponse.from_appointment(appointment)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment_endpoint(
    appointment_id: str,
    session: Session = Depends(get_db),
) -> None:
    appointment_service.delete_appointment(
        session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
    )
