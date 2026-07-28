"""Routine API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.clock import SystemClock
from planforge.domain.enums import OccurrenceStatus, RoutineStatus
from planforge.domain.local_date import LocalDate
from planforge.models.occurrence import Occurrence
from planforge.models.routine import Routine
from planforge.services import routine_service
from planforge.services.occurrence_generator import SCHEDULE_MONTHLY, SCHEDULE_WEEKLY
from planforge.services.settings_service import get_policy_snapshot

router = APIRouter(prefix="/routines", tags=["routines"])


class RoutineCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str | None = None
    schedule_type: str = SCHEDULE_WEEKLY
    days_of_week: list[int] | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    interval_weeks: int = Field(default=1, ge=1, le=52)
    starts_on: date | None = None


class RoutineUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    notes: str | None = None
    schedule_type: str | None = None
    days_of_week: list[int] | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    interval_weeks: int | None = Field(default=None, ge=1, le=52)
    starts_on: date | None = None


class RoutineResponse(BaseModel):
    id: str
    title: str
    notes: str | None
    schedule_type: str
    days_of_week: list[int]
    day_of_month: int | None
    interval_weeks: int
    starts_on: date | None
    status: RoutineStatus

    @classmethod
    def from_routine(cls, routine: Routine) -> RoutineResponse:
        from planforge.services.occurrence_generator import parse_days_of_week

        return cls(
            id=routine.id,
            title=routine.title,
            notes=routine.notes,
            schedule_type=routine.schedule_type,
            days_of_week=parse_days_of_week(routine.days_of_week),
            day_of_month=routine.day_of_month,
            interval_weeks=routine.interval_weeks,
            starts_on=routine.starts_on,
            status=routine.routine_status,
        )


class OccurrenceResponse(BaseModel):
    id: str
    routine_id: str
    scheduled_date: str
    status: OccurrenceStatus

    @classmethod
    def from_occurrence(cls, occurrence: Occurrence) -> OccurrenceResponse:
        return cls(
            id=occurrence.id,
            routine_id=occurrence.routine_id,
            scheduled_date=occurrence.scheduled_date.isoformat(),
            status=occurrence.occurrence_status,
        )


@router.get("", response_model=list[RoutineResponse])
def list_routines_endpoint(session: Session = Depends(get_db)) -> list[RoutineResponse]:
    routines = routine_service.list_routines(session, owner_id=LOCAL_OWNER_ID)
    return [RoutineResponse.from_routine(routine) for routine in routines]


@router.post("", response_model=RoutineResponse, status_code=status.HTTP_201_CREATED)
def create_routine_endpoint(
    body: RoutineCreateRequest,
    session: Session = Depends(get_db),
) -> RoutineResponse:
    clock = SystemClock()
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    starts_on = (
        LocalDate.from_date(body.starts_on) if body.starts_on is not None else None
    )
    routine = routine_service.create_routine(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
        schedule_type=body.schedule_type,
        days_of_week=body.days_of_week,
        day_of_month=body.day_of_month,
        interval_weeks=body.interval_weeks,
        starts_on=starts_on,
        clock_today=clock.today(),
    )
    routine_service.ensure_occurrences(
        session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=clock.today(),
        policies=policies,
    )
    return RoutineResponse.from_routine(routine)


@router.patch("/{routine_id}", response_model=RoutineResponse)
def update_routine_endpoint(
    routine_id: str,
    body: RoutineUpdateRequest,
    session: Session = Depends(get_db),
) -> RoutineResponse:
    clock = SystemClock()
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    starts_on_value: LocalDate | None | object = routine_service.UNSET
    if "starts_on" in body.model_fields_set:
        starts_on_value = (
            LocalDate.from_date(body.starts_on) if body.starts_on is not None else None
        )

    routine = routine_service.update_routine(
        session,
        routine_id=routine_id,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes if "notes" in body.model_fields_set else routine_service.UNSET,
        schedule_type=body.schedule_type,
        days_of_week=body.days_of_week,
        day_of_month=(
            body.day_of_month
            if "day_of_month" in body.model_fields_set
            else routine_service.UNSET
        ),
        interval_weeks=body.interval_weeks,
        starts_on=starts_on_value,
        clock_today=clock.today(),
        policies=policies,
    )
    return RoutineResponse.from_routine(routine)


@router.post("/{routine_id}/pause", response_model=RoutineResponse)
def pause_routine_endpoint(
    routine_id: str,
    session: Session = Depends(get_db),
) -> RoutineResponse:
    routine = routine_service.pause_routine(
        session,
        routine_id=routine_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return RoutineResponse.from_routine(routine)


@router.post("/{routine_id}/resume", response_model=RoutineResponse)
def resume_routine_endpoint(
    routine_id: str,
    session: Session = Depends(get_db),
) -> RoutineResponse:
    clock = SystemClock()
    policies = get_policy_snapshot(session, owner_id=LOCAL_OWNER_ID)
    routine = routine_service.resume_routine(
        session,
        routine_id=routine_id,
        owner_id=LOCAL_OWNER_ID,
    )
    routine_service.ensure_occurrences(
        session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=clock.today(),
        policies=policies,
    )
    return RoutineResponse.from_routine(routine)


@router.post("/{routine_id}/archive", response_model=RoutineResponse)
def archive_routine_endpoint(
    routine_id: str,
    session: Session = Depends(get_db),
) -> RoutineResponse:
    routine = routine_service.archive_routine(
        session,
        routine_id=routine_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return RoutineResponse.from_routine(routine)


@router.post("/occurrences/{occurrence_id}/complete", response_model=OccurrenceResponse)
def complete_occurrence_endpoint(
    occurrence_id: str,
    session: Session = Depends(get_db),
) -> OccurrenceResponse:
    occurrence = routine_service.complete_occurrence(
        session,
        occurrence_id=occurrence_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return OccurrenceResponse.from_occurrence(occurrence)


@router.post("/occurrences/{occurrence_id}/skip", response_model=OccurrenceResponse)
def skip_occurrence_endpoint(
    occurrence_id: str,
    session: Session = Depends(get_db),
) -> OccurrenceResponse:
    occurrence = routine_service.skip_occurrence(
        session,
        occurrence_id=occurrence_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return OccurrenceResponse.from_occurrence(occurrence)
