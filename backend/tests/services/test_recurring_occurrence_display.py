"""Tests for recurring occurrence display selection."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.local_date import LocalDate
from planforge.domain.recurring_display import (
    DEFAULT_RECURRING_DISPLAY_POLICY,
    OccurrenceDisplayRole,
)
from planforge.services import routine_service
from planforge.services.recurring_occurrence_display import (
    select_visible_routine_occurrences,
)
from planforge.services.settings_service import PolicySnapshot
from planforge.services.week_bounds import week_bounds
from planforge.services.week_view import assemble_week_view


def _seed_weekly_routine(db_session, *, title: str, today: LocalDate) -> None:
    routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title=title,
        days_of_week=[3],
        clock_today=today,
    )
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=PolicySnapshot(routine_horizon_days=30),
    )


def test_weekly_routine_limits_upcoming_to_current_plus_next(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    week_start, _ = week_bounds(reference_date=today, week_start_day="monday")
    _seed_weekly_routine(db_session, title="Change sheets", today=today)

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=PolicySnapshot(),
    )

    routine_items = [
        item
        for group in view.days
        for item in group.items
        if item.kind.value == "occurrence"
    ]
    assert len(routine_items) <= 2
    upcoming = next(group for group in view.days if group.label == "upcoming")
    routine_upcoming = [
        item for item in upcoming.items if item.kind.value == "occurrence"
    ]
    assert len(routine_upcoming) <= 1


def test_multi_weekday_routine_shows_at_most_two_occurrences(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Daily stretch",
        days_of_week=[0, 1, 2, 3, 4],
        clock_today=today,
    )
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=PolicySnapshot(routine_horizon_days=14),
    )

    horizon_start, horizon_end = DEFAULT_RECURRING_DISPLAY_POLICY.horizon_bounds(
        today=today,
        week_start_day="monday",
    )
    visible = select_visible_routine_occurrences(
        routine_service.list_pending_occurrences(db_session, owner_id=LOCAL_OWNER_ID),
        today=today,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )
    daily = [item for item in visible if item.routine.title == "Daily stretch"]
    assert len(daily) == 2
    assert daily[0].role is OccurrenceDisplayRole.CURRENT
    assert daily[1].role is OccurrenceDisplayRole.NEXT


def test_overdue_plus_future_limits_to_three_slots(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    clock_start = LocalDate.from_iso("2026-07-02")
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Change sheets",
        days_of_week=[3],
        clock_today=clock_start,
    )
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=clock_start,
        policies=PolicySnapshot(routine_horizon_days=30),
    )
    horizon_start, horizon_end = DEFAULT_RECURRING_DISPLAY_POLICY.horizon_bounds(
        today=today,
        week_start_day="monday",
    )
    visible = select_visible_routine_occurrences(
        routine_service.list_pending_occurrences(db_session, owner_id=LOCAL_OWNER_ID),
        today=today,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )
    sheets = [item for item in visible if item.routine.id == routine.id]
    assert len(sheets) == 3
    assert sheets[0].role is OccurrenceDisplayRole.OVERDUE
    assert sheets[1].role is OccurrenceDisplayRole.CURRENT
    assert sheets[2].role is OccurrenceDisplayRole.NEXT


def test_complete_earliest_advances_display(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    _seed_weekly_routine(db_session, title="Change sheets", today=today)
    first, _ = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )[0]
    routine_service.complete_occurrence(
        db_session,
        occurrence_id=first.id,
        owner_id=LOCAL_OWNER_ID,
    )

    horizon_start, horizon_end = DEFAULT_RECURRING_DISPLAY_POLICY.horizon_bounds(
        today=today,
        week_start_day="monday",
    )
    visible = select_visible_routine_occurrences(
        routine_service.list_pending_occurrences(db_session, owner_id=LOCAL_OWNER_ID),
        today=today,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )
    assert len(visible) == 1
    assert visible[0].scheduled.to_iso() == "2026-07-30"
    assert visible[0].role is OccurrenceDisplayRole.CURRENT


def test_skip_earliest_advances_display(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    _seed_weekly_routine(db_session, title="Change sheets", today=today)
    first, _ = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )[0]
    routine_service.skip_occurrence(
        db_session,
        occurrence_id=first.id,
        owner_id=LOCAL_OWNER_ID,
    )

    horizon_start, horizon_end = DEFAULT_RECURRING_DISPLAY_POLICY.horizon_bounds(
        today=today,
        week_start_day="monday",
    )
    visible = select_visible_routine_occurrences(
        routine_service.list_pending_occurrences(db_session, owner_id=LOCAL_OWNER_ID),
        today=today,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )
    assert visible[0].scheduled.to_iso() == "2026-07-30"


def test_multiple_routines_each_get_their_own_slots(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    _seed_weekly_routine(db_session, title="Change sheets", today=today)
    _seed_weekly_routine(db_session, title="Water plants", today=today)

    horizon_start, horizon_end = DEFAULT_RECURRING_DISPLAY_POLICY.horizon_bounds(
        today=today,
        week_start_day="monday",
    )
    visible = select_visible_routine_occurrences(
        routine_service.list_pending_occurrences(db_session, owner_id=LOCAL_OWNER_ID),
        today=today,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )
    titles = {item.routine.title for item in visible}
    assert titles == {"Change sheets", "Water plants"}
    assert len(visible) == 4


def test_tasks_and_appointments_unaffected_in_week_view(db_session) -> None:
    from datetime import UTC, datetime

    from planforge.models.appointment import Appointment
    from planforge.models.task import Task

    today = LocalDate.from_iso("2026-07-20")
    week_start, _ = week_bounds(reference_date=today, week_start_day="monday")
    _seed_weekly_routine(db_session, title="Change sheets", today=today)

    db_session.add(
        Task(
            owner_id=LOCAL_OWNER_ID,
            title="Later task",
            due_date=LocalDate.from_iso("2026-08-15").to_date(),
            status="pending",
        )
    )
    db_session.add(
        Appointment(
            owner_id=LOCAL_OWNER_ID,
            title="Future appointment",
            is_all_day=False,
            start_date=datetime(2026, 8, 15, 15, 0, tzinfo=UTC).date(),
            end_date=datetime(2026, 8, 15, 16, 0, tzinfo=UTC).date(),
            starts_at=datetime(2026, 8, 15, 15, 0, tzinfo=UTC),
            ends_at=datetime(2026, 8, 15, 16, 0, tzinfo=UTC),
            status="scheduled",
        )
    )
    db_session.flush()

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=PolicySnapshot(),
    )
    upcoming = next(group for group in view.days if group.label == "upcoming")
    kinds = {item.kind.value for item in upcoming.items}
    assert "task" in kinds
    assert "appointment" in kinds
    assert (
        len([item for item in upcoming.items if item.kind.value == "occurrence"]) <= 1
    )


def test_sunday_week_start_horizon(db_session) -> None:
    today = LocalDate.from_iso("2026-07-22")
    horizon_start, horizon_end = DEFAULT_RECURRING_DISPLAY_POLICY.horizon_bounds(
        today=today,
        week_start_day="sunday",
    )
    assert horizon_start.to_iso() == "2026-07-19"
    assert horizon_end.to_iso() == "2026-08-01"
