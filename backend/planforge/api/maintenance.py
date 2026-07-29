"""Maintenance API endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import MaintenanceListFilter, MaintenanceStatus
from planforge.domain.local_date import LocalDate
from planforge.domain.planner_clock import PlannerClock
from planforge.models.appointment import Appointment
from planforge.models.maintenance import MaintenanceDefinition
from planforge.models.maintenance_completion import MaintenanceCompletion
from planforge.schemas.appointment import AppointmentResponse
from planforge.schemas.maintenance import (
    MaintenanceCompleteRequest,
    MaintenanceCompletionResponse,
    MaintenanceCorrectCompletionRequest,
    MaintenanceCreateRequest,
    MaintenanceDetailResponse,
    MaintenanceHistoricalCompletionRequest,
    MaintenanceHistoryBoardResponse,
    MaintenanceHistoryRowResponse,
    MaintenanceLinkAppointmentRequest,
    MaintenanceResponse,
    MaintenanceScheduleAppointmentRequest,
    MaintenanceSchedulingReminderRequest,
    MaintenanceUpdateRequest,
)
from planforge.services import maintenance_service
from planforge.services.maintenance_service import UNSET
from planforge.services.settings_service import get_policy_snapshot

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


def _current_next_label(
    item: MaintenanceDefinition,
    linked: Appointment | None = None,
) -> str:
    from planforge.domain.enums import MaintenanceNextActionStatus

    if item.next_action is MaintenanceNextActionStatus.SCHEDULED:
        if linked is not None:
            return f"Scheduled {linked.start_date.strftime('%b %d')}"
        return "Scheduled"
    if item.next_action is MaintenanceNextActionStatus.NEEDS_SCHEDULING:
        if item.next_due_date:
            return f"Due {item.next_due_date.strftime('%b %Y')}"
        return "Needs scheduling"
    if item.next_action is MaintenanceNextActionStatus.REMINDER_SET:
        if item.scheduling_reminder_date:
            return f"Remind {item.scheduling_reminder_date.isoformat()}"
        return "Reminder set"
    if item.next_action is MaintenanceNextActionStatus.NOT_APPLICABLE:
        return "Archived"
    return "No next date"


@router.get("", response_model=list[MaintenanceResponse])
def list_maintenance_endpoint(
    session: Session = Depends(get_db),
    list_filter: MaintenanceListFilter | None = Query(default=None, alias="filter"),
    status_filter: MaintenanceStatus | None = Query(default=None, alias="status"),
) -> list[MaintenanceResponse]:
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    clock = PlannerClock(policies.timezone)
    items = maintenance_service.list_maintenance(
        session,
        owner_id=LOCAL_OWNER_ID,
        list_filter=list_filter,
        status=status_filter,
        today=clock.today(),
    )
    return [MaintenanceResponse.from_item(item) for item in items]


@router.get("/history-board", response_model=MaintenanceHistoryBoardResponse)
def maintenance_history_board_endpoint(
    session: Session = Depends(get_db),
    history_limit: int = Query(default=10, ge=1, le=500),
) -> MaintenanceHistoryBoardResponse:
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    clock = PlannerClock(policies.timezone)
    board = maintenance_service.build_history_board(
        session,
        owner_id=LOCAL_OWNER_ID,
        today=clock.today(),
        history_limit=history_limit,
    )
    rows: list[MaintenanceHistoryRowResponse] = []
    for entry in board:
        item = entry["maintenance"]
        assert isinstance(item, MaintenanceDefinition)
        linked = entry.get("linked_appointment")
        completions_raw = entry["completions"]
        assert isinstance(completions_raw, list)
        completions = [
            completion
            for completion in completions_raw
            if isinstance(completion, MaintenanceCompletion)
        ]
        rows.append(
            MaintenanceHistoryRowResponse(
                maintenance=MaintenanceResponse.from_item(item),
                current_next_label=_current_next_label(
                    item, linked if isinstance(linked, Appointment) else None
                ),
                completions=[
                    MaintenanceCompletionResponse.from_completion(c)
                    for c in completions
                ],
                linked_appointment=(
                    AppointmentResponse.from_appointment(linked)
                    if isinstance(linked, Appointment)
                    else None
                ),
            )
        )
    return MaintenanceHistoryBoardResponse(rows=rows, history_limit=history_limit)


@router.post(
    "", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED
)
def create_maintenance_endpoint(
    body: MaintenanceCreateRequest,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.create_maintenance(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        category=body.category,
        notes=body.notes,
        interval_unit=body.interval_unit,
        interval_value=body.interval_value,
        lead_time_days=body.lead_time_days,
        reminder_offset_days=body.reminder_offset_days,
    )
    return MaintenanceResponse.from_item(item)


@router.get("/{maintenance_id}", response_model=MaintenanceDetailResponse)
def get_maintenance_endpoint(
    maintenance_id: str,
    session: Session = Depends(get_db),
    history_limit: int = Query(default=25, ge=1, le=500),
) -> MaintenanceDetailResponse:
    item = maintenance_service.get_maintenance(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
    )
    linked = None
    if item.linked_appointment_id:
        linked = session.get(Appointment, item.linked_appointment_id)
    completions = maintenance_service.list_completions(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
        limit=history_limit,
    )
    return MaintenanceDetailResponse.from_item(
        item,
        linked_appointment=linked,
        completions=completions,
    )


@router.patch("/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance_endpoint(
    maintenance_id: str,
    body: MaintenanceUpdateRequest,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.update_maintenance(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
        title=body.title if "title" in body.model_fields_set else UNSET,
        category=body.category if "category" in body.model_fields_set else UNSET,
        notes=body.notes if "notes" in body.model_fields_set else UNSET,
        interval_unit=(
            body.interval_unit if "interval_unit" in body.model_fields_set else UNSET
        ),
        interval_value=(
            body.interval_value if "interval_value" in body.model_fields_set else UNSET
        ),
        lead_time_days=(
            body.lead_time_days if "lead_time_days" in body.model_fields_set else UNSET
        ),
        reminder_offset_days=(
            body.reminder_offset_days
            if "reminder_offset_days" in body.model_fields_set
            else UNSET
        ),
    )
    return MaintenanceResponse.from_item(item)


@router.post("/{maintenance_id}/archive", response_model=MaintenanceResponse)
def archive_maintenance_endpoint(
    maintenance_id: str,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.archive_maintenance(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return MaintenanceResponse.from_item(item)


@router.post("/{maintenance_id}/restore", response_model=MaintenanceResponse)
def restore_maintenance_endpoint(
    maintenance_id: str,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.restore_maintenance(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return MaintenanceResponse.from_item(item)


@router.post("/{maintenance_id}/complete", response_model=MaintenanceResponse)
def complete_maintenance_endpoint(
    maintenance_id: str,
    body: MaintenanceCompleteRequest | None = None,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    completed_on = (
        LocalDate.from_date(body.completed_on)
        if body and body.completed_on is not None
        else None
    )
    item = maintenance_service.complete_maintenance(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=completed_on,
        notes=body.notes if body else None,
    )
    return MaintenanceResponse.from_item(item)


@router.post(
    "/{maintenance_id}/completions",
    response_model=MaintenanceCompletionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_historical_completion_endpoint(
    maintenance_id: str,
    body: MaintenanceHistoricalCompletionRequest,
    session: Session = Depends(get_db),
) -> MaintenanceCompletionResponse:
    completion = maintenance_service.add_historical_completion(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_date(body.completed_on),
        notes=body.notes,
    )
    return MaintenanceCompletionResponse.from_completion(completion)


@router.post(
    "/{maintenance_id}/completions/{completion_id}/correct",
    response_model=MaintenanceCompletionResponse,
)
def correct_completion_endpoint(
    maintenance_id: str,
    completion_id: str,
    body: MaintenanceCorrectCompletionRequest,
    session: Session = Depends(get_db),
) -> MaintenanceCompletionResponse:
    completion = maintenance_service.correct_completion(
        session,
        maintenance_id=maintenance_id,
        completion_id=completion_id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_date(body.completed_on),
        notes=body.notes,
        void_reason=body.void_reason,
    )
    return MaintenanceCompletionResponse.from_completion(completion)


@router.post("/{maintenance_id}/link-appointment", response_model=MaintenanceResponse)
def link_appointment_endpoint(
    maintenance_id: str,
    body: MaintenanceLinkAppointmentRequest,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.link_appointment(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
        appointment_id=body.appointment_id,
    )
    return MaintenanceResponse.from_item(item)


@router.post(
    "/{maintenance_id}/schedule-appointment",
    response_model=MaintenanceDetailResponse,
)
def schedule_appointment_endpoint(
    maintenance_id: str,
    body: MaintenanceScheduleAppointmentRequest,
    session: Session = Depends(get_db),
) -> MaintenanceDetailResponse:
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    item, appointment = maintenance_service.schedule_appointment(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        start_date=LocalDate.from_date(body.start_date),
        end_date=LocalDate.from_date(body.end_date),
        is_all_day=body.is_all_day,
        start_time=body.start_time,
        end_time=body.end_time,
        timezone_name=policies.timezone,
        location=body.location,
        notes=body.notes,
    )
    return MaintenanceDetailResponse.from_item(
        item,
        linked_appointment=appointment,
        completions=maintenance_service.list_completions(
            session,
            maintenance_id=maintenance_id,
            owner_id=LOCAL_OWNER_ID,
            limit=25,
        ),
    )


@router.post(
    "/{maintenance_id}/reschedule-appointment",
    response_model=MaintenanceResponse,
)
def reschedule_linked_appointment_endpoint(
    maintenance_id: str,
    body: MaintenanceScheduleAppointmentRequest,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    item = maintenance_service.reschedule_linked_appointment(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
        is_all_day=body.is_all_day,
        start_date=LocalDate.from_date(body.start_date),
        end_date=LocalDate.from_date(body.end_date),
        start_time=body.start_time,
        end_time=body.end_time,
        timezone_name=policies.timezone,
    )
    return MaintenanceResponse.from_item(item)


@router.post(
    "/{maintenance_id}/scheduling-reminder",
    response_model=MaintenanceResponse,
)
def set_scheduling_reminder_endpoint(
    maintenance_id: str,
    body: MaintenanceSchedulingReminderRequest,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.set_scheduling_reminder(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
        reminder_date=LocalDate.from_date(body.reminder_date),
    )
    return MaintenanceResponse.from_item(item)


@router.delete(
    "/{maintenance_id}/scheduling-reminder",
    response_model=MaintenanceResponse,
)
def clear_scheduling_reminder_endpoint(
    maintenance_id: str,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.clear_scheduling_reminder(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return MaintenanceResponse.from_item(item)


@router.post("/{maintenance_id}/clear-next-action", response_model=MaintenanceResponse)
def clear_next_action_endpoint(
    maintenance_id: str,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.clear_next_action(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return MaintenanceResponse.from_item(item)
