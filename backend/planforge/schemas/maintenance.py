"""Pydantic schemas for maintenance."""

from datetime import date, time

from planforge.domain.enums import (
    MaintenanceIntervalUnit,
    MaintenanceListFilter,
    MaintenanceNextActionStatus,
    MaintenanceStatus,
)
from planforge.models.appointment import Appointment
from planforge.models.maintenance import MaintenanceDefinition
from planforge.models.maintenance_completion import MaintenanceCompletion
from planforge.schemas.appointment import AppointmentResponse
from pydantic import BaseModel, Field


class MaintenanceCompletionResponse(BaseModel):
    id: str
    completed_on: date
    notes: str | None
    is_voided: bool
    superseded_by_id: str | None

    @classmethod
    def from_completion(
        cls,
        completion: MaintenanceCompletion,
    ) -> MaintenanceCompletionResponse:
        return cls(
            id=completion.id,
            completed_on=completion.completed_on,
            notes=completion.notes,
            is_voided=completion.is_voided,
            superseded_by_id=completion.superseded_by_id,
        )


class MaintenanceResponse(BaseModel):
    id: str
    title: str
    category: str | None
    notes: str | None
    interval_unit: MaintenanceIntervalUnit
    interval_value: int | None
    last_completed_date: date | None
    next_due_date: date | None
    next_action_status: MaintenanceNextActionStatus
    linked_appointment_id: str | None
    scheduling_reminder_date: date | None
    reminder_offset_days: int | None
    lead_time_days: int
    status: MaintenanceStatus

    @classmethod
    def from_item(cls, item: MaintenanceDefinition) -> MaintenanceResponse:
        return cls(
            id=item.id,
            title=item.title,
            category=item.category,
            notes=item.notes,
            interval_unit=item.interval,
            interval_value=item.interval_value,
            last_completed_date=item.last_completed_date,
            next_due_date=item.next_due_date,
            next_action_status=item.next_action,
            linked_appointment_id=item.linked_appointment_id,
            scheduling_reminder_date=item.scheduling_reminder_date,
            reminder_offset_days=item.reminder_offset_days,
            lead_time_days=item.lead_time_days,
            status=item.maintenance_status,
        )


class MaintenanceDetailResponse(MaintenanceResponse):
    linked_appointment: AppointmentResponse | None = None
    completions: list[MaintenanceCompletionResponse] = Field(default_factory=list)

    @classmethod
    def from_item(
        cls,
        item: MaintenanceDefinition,
        *,
        linked_appointment: Appointment | None = None,
        completions: list[MaintenanceCompletion] | None = None,
    ) -> MaintenanceDetailResponse:
        base = MaintenanceResponse.from_item(item)
        return cls(
            **base.model_dump(),
            linked_appointment=(
                AppointmentResponse.from_appointment(linked_appointment)
                if linked_appointment is not None
                else None
            ),
            completions=[
                MaintenanceCompletionResponse.from_completion(completion)
                for completion in (completions or [])
            ],
        )


class MaintenanceCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    category: str | None = None
    notes: str | None = None
    interval_unit: MaintenanceIntervalUnit = MaintenanceIntervalUnit.MONTHS
    interval_value: int | None = Field(default=6, ge=1)
    lead_time_days: int = Field(default=30, ge=0)
    reminder_offset_days: int | None = Field(default=None, ge=0)


class MaintenanceUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    category: str | None = None
    notes: str | None = None
    interval_unit: MaintenanceIntervalUnit | None = None
    interval_value: int | None = Field(default=None, ge=1)
    lead_time_days: int | None = Field(default=None, ge=0)
    reminder_offset_days: int | None = Field(default=None, ge=0)


class MaintenanceCompleteRequest(BaseModel):
    completed_on: date | None = None
    notes: str | None = None


class MaintenanceHistoricalCompletionRequest(BaseModel):
    completed_on: date
    notes: str | None = None


class MaintenanceCorrectCompletionRequest(BaseModel):
    completed_on: date
    notes: str | None = None
    void_reason: str | None = None


class MaintenanceLinkAppointmentRequest(BaseModel):
    appointment_id: str


class MaintenanceScheduleAppointmentRequest(BaseModel):
    title: str | None = None
    notes: str | None = None
    location: str | None = None
    is_all_day: bool = False
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None


class MaintenanceSchedulingReminderRequest(BaseModel):
    reminder_date: date


class MaintenanceHistoryRowResponse(BaseModel):
    maintenance: MaintenanceResponse
    current_next_label: str
    completions: list[MaintenanceCompletionResponse]
    linked_appointment: AppointmentResponse | None = None


class MaintenanceHistoryBoardResponse(BaseModel):
    rows: list[MaintenanceHistoryRowResponse]
    history_limit: int


class MaintenanceListQuery(BaseModel):
    list_filter: MaintenanceListFilter | None = None
    status: MaintenanceStatus | None = None
