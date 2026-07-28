"""Tests for routine occurrence generation."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import RoutineStatus
from planforge.domain.local_date import LocalDate
from planforge.services import routine_service
from planforge.services.settings_service import PolicySnapshot


def test_active_routine_generates_weekday_occurrences(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Weekday demo stretch",
        days_of_week=[0, 1, 2, 3, 4],
        clock_today=today,
    )
    policies = PolicySnapshot(routine_horizon_days=7)
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=policies,
    )
    pending = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )
    assert len(pending) >= 5
    assert all(occurrence.routine_id == routine.id for occurrence, _ in pending)


def test_paused_routine_generates_nothing_new(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Paused demo",
        days_of_week=[0, 1, 2, 3, 4],
        clock_today=today,
    )
    routine_service.pause_routine(
        db_session,
        routine_id=routine.id,
        owner_id=LOCAL_OWNER_ID,
    )
    policies = PolicySnapshot(routine_horizon_days=7)
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=policies,
    )
    pending = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )
    assert pending == []


def test_complete_occurrence_keeps_routine(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Weekday demo stretch",
        days_of_week=[0],
        clock_today=today,
    )
    policies = PolicySnapshot(routine_horizon_days=7)
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=policies,
    )
    occurrence, _ = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )[0]
    routine_service.complete_occurrence(
        db_session,
        occurrence_id=occurrence.id,
        owner_id=LOCAL_OWNER_ID,
    )
    routines = routine_service.list_routines(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        status=RoutineStatus.ACTIVE,
    )
    assert len(routines) == 1


def test_update_routine_changes_future_schedule(db_session) -> None:
    today = LocalDate.from_iso("2026-07-27")
    policies = PolicySnapshot(routine_horizon_days=14)
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Stretch",
        days_of_week=[0, 1, 2, 3, 4],
        clock_today=today,
    )
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=policies,
    )
    routine_service.update_routine(
        db_session,
        routine_id=routine.id,
        owner_id=LOCAL_OWNER_ID,
        days_of_week=[3],
        clock_today=today,
        policies=policies,
    )
    pending = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )
    weekdays = {
        LocalDate.from_date(occurrence.scheduled_date).weekday()
        for occurrence, _ in pending
    }
    assert weekdays == {3}
