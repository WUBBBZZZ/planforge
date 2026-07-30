"""Routine and occurrence business logic."""

import json
from datetime import UTC, datetime
from typing import Any

from planforge.core.exceptions import (
    OccurrenceNotFoundError,
    OccurrenceStateError,
    RoutineNotFoundError,
    RoutineStateError,
    ValidationError,
)
from planforge.domain.enums import CompletionAction, OccurrenceStatus, RoutineStatus
from planforge.domain.local_date import LocalDate
from planforge.models.completion_record import CompletionRecord
from planforge.models.occurrence import Occurrence
from planforge.models.routine import Routine
from planforge.services import routine_group_service
from planforge.services.occurrence_generator import (
    SCHEDULE_MONTHLY,
    SCHEDULE_WEEKLY,
    horizon_end,
    routine_effective_start,
    schedule_dates_for_routine,
)
from planforge.services.settings_service import PolicySnapshot
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

_UNSET: Any = object()
UNSET = _UNSET


def _get_routine_or_raise(
    session: Session,
    *,
    routine_id: str,
    owner_id: str,
) -> Routine:
    routine = session.scalar(
        select(Routine).where(
            Routine.id == routine_id,
            Routine.owner_id == owner_id,
        )
    )
    if routine is None:
        raise RoutineNotFoundError(f"Routine not found: {routine_id}")
    return routine


def _get_occurrence_or_raise(
    session: Session,
    *,
    occurrence_id: str,
    owner_id: str,
) -> Occurrence:
    occurrence = session.scalar(
        select(Occurrence).where(
            Occurrence.id == occurrence_id,
            Occurrence.owner_id == owner_id,
        )
    )
    if occurrence is None:
        raise OccurrenceNotFoundError(f"Occurrence not found: {occurrence_id}")
    return occurrence


def _append_completion(
    session: Session,
    *,
    owner_id: str,
    entity_type: str,
    entity_id: str,
    action: CompletionAction,
) -> None:
    session.add(
        CompletionRecord(
            owner_id=owner_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action.value,
            recorded_at=datetime.now(UTC),
        )
    )


def _validate_schedule(
    *,
    schedule_type: str,
    days_of_week: list[int] | None,
    day_of_month: int | None,
    interval_weeks: int | None,
) -> None:
    if schedule_type not in {SCHEDULE_WEEKLY, SCHEDULE_MONTHLY}:
        raise ValidationError("schedule_type must be weekly or monthly")
    if schedule_type == SCHEDULE_WEEKLY:
        if not days_of_week:
            raise ValidationError("days_of_week is required for weekly routines")
        if any(day < 0 or day > 6 for day in days_of_week):
            raise ValidationError("days_of_week values must be 0-6")
        if interval_weeks is not None and interval_weeks < 1:
            raise ValidationError("interval_weeks must be at least 1")
    if schedule_type == SCHEDULE_MONTHLY:
        if day_of_month is None:
            raise ValidationError("day_of_month is required for monthly routines")
        if day_of_month < 1 or day_of_month > 31:
            raise ValidationError("day_of_month must be between 1 and 31")


def create_routine(
    session: Session,
    *,
    owner_id: str,
    title: str,
    notes: str | None = None,
    schedule_type: str = SCHEDULE_WEEKLY,
    days_of_week: list[int] | None = None,
    day_of_month: int | None = None,
    interval_weeks: int = 1,
    starts_on: LocalDate | None = None,
    clock_today: LocalDate | None = None,
) -> Routine:
    """Create an active routine."""
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValidationError("Title must not be empty")

    weekly_days = days_of_week or [0, 1, 2, 3, 4]
    _validate_schedule(
        schedule_type=schedule_type,
        days_of_week=weekly_days,
        day_of_month=day_of_month,
        interval_weeks=interval_weeks,
    )

    effective_start = starts_on or clock_today
    misc = routine_group_service.get_misc_group(session, owner_id=owner_id)
    max_sort = session.scalar(
        select(func.max(Routine.sort_order)).where(Routine.group_id == misc.id)
    )
    routine = Routine(
        owner_id=owner_id,
        title=cleaned_title,
        notes=notes,
        schedule_type=schedule_type,
        days_of_week=json.dumps(weekly_days),
        day_of_month=day_of_month,
        interval_weeks=interval_weeks,
        starts_on=effective_start.to_date() if effective_start else None,
        status=RoutineStatus.ACTIVE.value,
        group_id=misc.id,
        sort_order=(max_sort or -1) + 1,
    )
    session.add(routine)
    session.flush()
    return routine


def update_routine(
    session: Session,
    *,
    routine_id: str,
    owner_id: str,
    title: str | None = None,
    notes: str | None | Any = UNSET,
    schedule_type: str | None = None,
    days_of_week: list[int] | None = None,
    day_of_month: int | None | Any = UNSET,
    interval_weeks: int | None = None,
    starts_on: LocalDate | None | Any = UNSET,
    clock_today: LocalDate,
    policies: PolicySnapshot,
) -> Routine:
    """Update a routine and refresh its future pending occurrences."""
    routine = _get_routine_or_raise(session, routine_id=routine_id, owner_id=owner_id)
    if routine.routine_status is RoutineStatus.ARCHIVED:
        raise RoutineStateError("Archived routines cannot be edited")

    if title is not None:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValidationError("Title must not be empty")
        routine.title = cleaned_title

    if notes is not UNSET:
        routine.notes = notes

    next_schedule_type = schedule_type or routine.schedule_type
    next_days = days_of_week
    if next_days is None and next_schedule_type == SCHEDULE_WEEKLY:
        from planforge.services.occurrence_generator import parse_days_of_week

        next_days = parse_days_of_week(routine.days_of_week)
    next_day_of_month = routine.day_of_month if day_of_month is UNSET else day_of_month
    next_interval = (
        interval_weeks if interval_weeks is not None else routine.interval_weeks
    )

    _validate_schedule(
        schedule_type=next_schedule_type,
        days_of_week=next_days,
        day_of_month=next_day_of_month,
        interval_weeks=next_interval,
    )

    routine.schedule_type = next_schedule_type
    if next_days is not None:
        routine.days_of_week = json.dumps(next_days)
    routine.day_of_month = next_day_of_month
    routine.interval_weeks = next_interval
    if starts_on is not UNSET:
        routine.starts_on = starts_on.to_date() if starts_on is not None else None

    session.flush()
    _refresh_future_occurrences(
        session,
        routine=routine,
        owner_id=owner_id,
        clock_today=clock_today,
        policies=policies,
    )
    return routine


def list_routines(
    session: Session,
    *,
    owner_id: str,
    status: RoutineStatus | None = None,
) -> list[Routine]:
    """List routines for an owner."""
    routine_group_service.ensure_default_groups(session, owner_id=owner_id)
    query = (
        select(Routine)
        .where(Routine.owner_id == owner_id)
        .order_by(Routine.sort_order, Routine.title)
    )
    if status is not None:
        query = query.where(Routine.status == status.value)
    return list(session.scalars(query))


def pause_routine(session: Session, *, routine_id: str, owner_id: str) -> Routine:
    """Pause an active routine."""
    routine = _get_routine_or_raise(session, routine_id=routine_id, owner_id=owner_id)
    if routine.routine_status is not RoutineStatus.ACTIVE:
        raise RoutineStateError("Only active routines can be paused")
    routine.status = RoutineStatus.PAUSED.value
    session.flush()
    return routine


def resume_routine(session: Session, *, routine_id: str, owner_id: str) -> Routine:
    """Resume a paused routine."""
    routine = _get_routine_or_raise(session, routine_id=routine_id, owner_id=owner_id)
    if routine.routine_status is not RoutineStatus.PAUSED:
        raise RoutineStateError("Only paused routines can be resumed")
    routine.status = RoutineStatus.ACTIVE.value
    session.flush()
    return routine


def archive_routine(session: Session, *, routine_id: str, owner_id: str) -> Routine:
    """Archive a routine."""
    routine = _get_routine_or_raise(session, routine_id=routine_id, owner_id=owner_id)
    if routine.routine_status is RoutineStatus.ARCHIVED:
        raise RoutineStateError("Routine is already archived")
    routine.status = RoutineStatus.ARCHIVED.value
    session.flush()
    return routine


def _generation_start(*, routine: Routine, clock_today: LocalDate) -> LocalDate:
    """First date to generate occurrences from (never before today or routine start)."""
    effective = routine_effective_start(routine)
    return effective if effective > clock_today else clock_today


def _cleanup_stale_pending_occurrences(
    session: Session,
    *,
    routine: Routine,
    owner_id: str,
) -> None:
    """Remove pending occurrences scheduled before the routine should have started."""
    effective = routine_effective_start(routine)
    session.execute(
        delete(Occurrence).where(
            Occurrence.routine_id == routine.id,
            Occurrence.owner_id == owner_id,
            Occurrence.status == OccurrenceStatus.PENDING.value,
            Occurrence.scheduled_date < effective.to_date(),
        )
    )


def _refresh_future_occurrences(
    session: Session,
    *,
    routine: Routine,
    owner_id: str,
    clock_today: LocalDate,
    policies: PolicySnapshot,
) -> None:
    """Drop and rebuild pending occurrences from today onward."""
    generation_start = _generation_start(routine=routine, clock_today=clock_today)
    delete_future_pending_occurrences(
        session,
        routine_id=routine.id,
        owner_id=owner_id,
        from_date=generation_start,
    )
    if routine.routine_status is RoutineStatus.ACTIVE:
        _generate_occurrences_for_routine(
            session,
            routine=routine,
            owner_id=owner_id,
            clock_today=clock_today,
            policies=policies,
        )
    session.flush()


def _generation_end_date(
    *,
    clock_today: LocalDate,
    horizon_days: int,
    through_date: LocalDate | None = None,
) -> LocalDate:
    """Return the inclusive last date to generate occurrences through."""
    end = horizon_end(today=clock_today, horizon_days=horizon_days)
    if through_date is not None and through_date > end:
        return through_date
    return end


def _generate_occurrences_for_routine(
    session: Session,
    *,
    routine: Routine,
    owner_id: str,
    clock_today: LocalDate,
    policies: PolicySnapshot,
    through_date: LocalDate | None = None,
) -> None:
    """Insert missing pending occurrences for one routine."""
    generation_start = _generation_start(routine=routine, clock_today=clock_today)
    end = _generation_end_date(
        clock_today=clock_today,
        horizon_days=policies.routine_horizon_days,
        through_date=through_date,
    )
    scheduled_dates = schedule_dates_for_routine(
        routine=routine,
        start=generation_start,
        end=end,
    )
    existing_dates = {
        LocalDate.from_date(row.scheduled_date)
        for row in session.scalars(
            select(Occurrence).where(
                Occurrence.routine_id == routine.id,
                Occurrence.owner_id == owner_id,
            )
        )
    }
    for scheduled_date in scheduled_dates:
        if scheduled_date in existing_dates:
            continue
        occurrence = Occurrence(
            owner_id=owner_id,
            routine_id=routine.id,
            scheduled_date=scheduled_date.to_date(),
            status=OccurrenceStatus.PENDING.value,
        )
        try:
            with session.begin_nested():
                session.add(occurrence)
                session.flush()
            existing_dates.add(scheduled_date)
        except IntegrityError:
            existing_dates.add(scheduled_date)


def ensure_occurrences(
    session: Session,
    *,
    owner_id: str,
    clock_today: LocalDate,
    policies: PolicySnapshot,
    through_date: LocalDate | None = None,
) -> None:
    """Generate pending occurrences for active routines within the horizon.

    When ``through_date`` is later than the configured horizon, generation extends
    through that date so calendar views can show routines in browsed future periods.
    """
    routines = list_routines(session, owner_id=owner_id, status=RoutineStatus.ACTIVE)
    for routine in routines:
        _cleanup_stale_pending_occurrences(session, routine=routine, owner_id=owner_id)
        _generate_occurrences_for_routine(
            session,
            routine=routine,
            owner_id=owner_id,
            clock_today=clock_today,
            policies=policies,
            through_date=through_date,
        )
    session.flush()


def list_pending_occurrences(
    session: Session,
    *,
    owner_id: str,
) -> list[tuple[Occurrence, Routine]]:
    """Return pending occurrences with their routines."""
    rows = session.execute(
        select(Occurrence, Routine)
        .join(Routine, Routine.id == Occurrence.routine_id)
        .where(
            Occurrence.owner_id == owner_id,
            Occurrence.status == OccurrenceStatus.PENDING.value,
            Routine.status != RoutineStatus.ARCHIVED.value,
        )
    )
    return [(occurrence, routine) for occurrence, routine in rows.all()]


def complete_occurrence(
    session: Session,
    *,
    occurrence_id: str,
    owner_id: str,
) -> Occurrence:
    """Mark an occurrence completed."""
    occurrence = _get_occurrence_or_raise(
        session,
        occurrence_id=occurrence_id,
        owner_id=owner_id,
    )
    if occurrence.occurrence_status is not OccurrenceStatus.PENDING:
        raise OccurrenceStateError("Only pending occurrences can be completed")
    occurrence.status = OccurrenceStatus.COMPLETED.value
    _append_completion(
        session,
        owner_id=owner_id,
        entity_type="occurrence",
        entity_id=occurrence.id,
        action=CompletionAction.COMPLETED,
    )
    session.flush()
    return occurrence


def skip_occurrence(
    session: Session,
    *,
    occurrence_id: str,
    owner_id: str,
) -> Occurrence:
    """Mark an occurrence skipped."""
    occurrence = _get_occurrence_or_raise(
        session,
        occurrence_id=occurrence_id,
        owner_id=owner_id,
    )
    if occurrence.occurrence_status is not OccurrenceStatus.PENDING:
        raise OccurrenceStateError("Only pending occurrences can be skipped")
    occurrence.status = OccurrenceStatus.SKIPPED.value
    _append_completion(
        session,
        owner_id=owner_id,
        entity_type="occurrence",
        entity_id=occurrence.id,
        action=CompletionAction.SKIPPED,
    )
    session.flush()
    return occurrence


def delete_future_pending_occurrences(
    session: Session,
    *,
    routine_id: str,
    owner_id: str,
    from_date: LocalDate,
) -> None:
    """Remove pending future occurrences from a date onward."""
    session.execute(
        delete(Occurrence).where(
            Occurrence.routine_id == routine_id,
            Occurrence.owner_id == owner_id,
            Occurrence.status == OccurrenceStatus.PENDING.value,
            Occurrence.scheduled_date >= from_date.to_date(),
        )
    )
    session.flush()
