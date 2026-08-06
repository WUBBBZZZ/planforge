"""Tests for recurring occurrence display selection."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.local_date import LocalDate
from planforge.domain.recurring_display import (
    DEFAULT_RECURRING_DISPLAY_POLICY,
    OccurrenceDisplayRole,
)
from planforge.services import routine_group_service, routine_service
from planforge.services.month_view import assemble_month_view
from planforge.services.recurring_occurrence_display import (
    routine_rolled_display_date,
    select_visible_routine_occurrences,
)
from planforge.services.settings_service import PolicySnapshot
from planforge.services.today_view import assemble_today_view
from planforge.services.week_bounds import week_bounds
from planforge.services.week_view import assemble_week_view


def test_routine_rolled_display_date_suppresses_when_next_occurrence_is_today() -> None:
    scheduled = LocalDate.from_iso("2026-07-27")
    today = LocalDate.from_iso("2026-07-28")
    next_scheduled = LocalDate.from_iso("2026-07-28")
    assert (
        routine_rolled_display_date(
            scheduled=scheduled,
            today=today,
            next_scheduled=next_scheduled,
        )
        is None
    )


def test_routine_rolled_display_date_rolls_until_day_before_next_occurrence() -> None:
    scheduled = LocalDate.from_iso("2026-07-22")
    today = LocalDate.from_iso("2026-07-25")
    next_scheduled = LocalDate.from_iso("2026-07-26")
    assert (
        routine_rolled_display_date(
            scheduled=scheduled,
            today=today,
            next_scheduled=next_scheduled,
        )
        == today
    )


def test_daily_missed_yesterday_shows_only_todays_occurrence(db_session) -> None:
    today = LocalDate.from_iso("2026-07-28")
    week_start, _ = week_bounds(reference_date=today, week_start_day="monday")
    routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Make bed",
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        clock_today=today.add_days(-1),
    )
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=PolicySnapshot(routine_horizon_days=14),
    )
    _show_all_routine_groups(db_session)

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=PolicySnapshot(),
    )

    tuesday_items = [
        item
        for group in view.days
        if group.date is not None and group.date.to_iso() == "2026-07-28"
        for item in group.items
        if item.kind.value == "occurrence" and item.title == "Make bed"
    ]
    assert len(tuesday_items) == 1
    assert tuesday_items[0].is_overdue is False


def test_twice_weekly_missed_first_rolls_until_day_before_second(db_session) -> None:
    clock_start = LocalDate.from_iso("2026-07-13")
    routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Check pantry",
        days_of_week=[2, 6],
        clock_today=clock_start,
    )
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=clock_start,
        policies=PolicySnapshot(routine_horizon_days=30),
    )
    _show_all_routine_groups(db_session)

    saturday = LocalDate.from_iso("2026-07-25")
    week_start, _ = week_bounds(reference_date=saturday, week_start_day="monday")
    saturday_view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=saturday,
        policies=PolicySnapshot(),
    )
    saturday_items = [
        item
        for group in saturday_view.days
        if group.date is not None and group.date.to_iso() == "2026-07-25"
        for item in group.items
        if item.kind.value == "occurrence" and item.title == "Check pantry"
    ]
    assert len(saturday_items) == 1
    assert saturday_items[0].is_overdue is True
    assert saturday_items[0].due_date.to_iso() == "2026-07-22"

    sunday = LocalDate.from_iso("2026-07-26")
    sunday_week_start, _ = week_bounds(reference_date=sunday, week_start_day="monday")
    sunday_view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=sunday_week_start,
        today=sunday,
        policies=PolicySnapshot(),
    )
    sunday_items = [
        item
        for group in sunday_view.days
        if group.date is not None and group.date.to_iso() == "2026-07-26"
        for item in group.items
        if item.kind.value == "occurrence" and item.title == "Check pantry"
    ]
    assert len(sunday_items) == 1
    assert sunday_items[0].is_overdue is False
    assert sunday_items[0].due_date.to_iso() == "2026-07-26"


def _show_all_routine_groups(db_session) -> None:
    """Enable week and month visibility for every routine group (hidden by default)."""
    routine_group_service.ensure_default_groups(db_session, owner_id=LOCAL_OWNER_ID)
    for group in routine_group_service.list_groups(db_session, owner_id=LOCAL_OWNER_ID):
        if not group.week_visible or not group.month_visible:
            routine_group_service.update_group(
                db_session,
                group_id=group.id,
                owner_id=LOCAL_OWNER_ID,
                week_visible=True,
                month_visible=True,
            )


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
    _show_all_routine_groups(db_session)

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=PolicySnapshot(),
    )

    calendar_routines = [
        item
        for group in view.days[:7]
        for item in group.items
        if item.kind.value == "occurrence"
    ]
    assert len(calendar_routines) == 1
    assert calendar_routines[0].due_date.to_iso() == "2026-07-23"

    upcoming = next((group for group in view.days if group.label == "upcoming"), None)
    if upcoming is not None:
        routine_upcoming = [
            item for item in upcoming.items if item.kind.value == "occurrence"
        ]
        assert len(routine_upcoming) == 0


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
    assert sheets[0].scheduled.to_iso() == "2026-07-16"
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
    _show_all_routine_groups(db_session)

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
        len([item for item in upcoming.items if item.kind.value == "occurrence"]) == 0
    )


def test_sunday_week_start_horizon(db_session) -> None:
    today = LocalDate.from_iso("2026-07-22")
    horizon_start, horizon_end = DEFAULT_RECURRING_DISPLAY_POLICY.horizon_bounds(
        today=today,
        week_start_day="sunday",
    )
    assert horizon_start.to_iso() == "2026-07-19"
    assert horizon_end.to_iso() == "2026-08-01"


def test_weekly_routine_appears_on_future_week_calendar(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    next_week_start, _ = week_bounds(
        reference_date=today.add_days(7),
        week_start_day="monday",
    )
    _seed_weekly_routine(db_session, title="Change sheets", today=today)
    _show_all_routine_groups(db_session)

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=next_week_start,
        today=today,
        policies=PolicySnapshot(),
    )

    calendar_routines = [
        item
        for group in view.days[:7]
        for item in group.items
        if item.kind.value == "occurrence"
    ]
    assert len(calendar_routines) == 1
    assert calendar_routines[0].due_date.to_iso() == "2026-07-30"


def test_weekly_routine_appears_on_future_month_calendar(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    august = LocalDate.from_iso("2026-08-01")
    routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Change sheets",
        days_of_week=[3],
        clock_today=today,
    )
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=PolicySnapshot(routine_horizon_days=60),
    )
    _show_all_routine_groups(db_session)

    view = assemble_month_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=august,
        clock_today=today,
        policies=PolicySnapshot(),
    )

    calendar_routines = [
        item
        for group in view.days
        if group.date is not None
        for item in group.items
        if item.kind.value == "occurrence"
    ]
    assert len(calendar_routines) == 4
    assert {item.due_date.to_iso() for item in calendar_routines} == {
        "2026-08-06",
        "2026-08-13",
        "2026-08-20",
        "2026-08-27",
    }


def test_routines_appear_in_month_beyond_default_horizon(db_session) -> None:
    today = LocalDate.from_iso("2026-07-30")
    september = LocalDate.from_iso("2026-09-01")
    _seed_weekly_routine(db_session, title="Change sheets", today=today)
    _show_all_routine_groups(db_session)

    view = assemble_month_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=september,
        clock_today=today,
        policies=PolicySnapshot(),
    )

    calendar_routines = [
        item
        for group in view.days
        if group.date is not None
        for item in group.items
        if item.kind.value == "occurrence"
    ]
    assert len(calendar_routines) == 4
    assert calendar_routines[0].due_date.to_iso() == "2026-09-03"


def test_routines_remain_on_current_views_after_browsing_future_month(
    db_session,
) -> None:
    today = LocalDate.from_iso("2026-07-30")
    august = LocalDate.from_iso("2026-08-01")
    _seed_weekly_routine(db_session, title="Change sheets", today=today)
    _show_all_routine_groups(db_session)

    assemble_month_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=august,
        clock_today=today,
        policies=PolicySnapshot(),
    )

    week_start, _ = week_bounds(reference_date=today, week_start_day="monday")
    week_view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=PolicySnapshot(),
    )
    week_routines = [
        item
        for group in week_view.days[:7]
        for item in group.items
        if item.kind.value == "occurrence"
    ]
    assert len(week_routines) == 1

    today_view = assemble_today_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=today,
        clock_today=today,
        policies=PolicySnapshot(),
    )
    today_routines = [
        item for item in today_view.items if item.kind.value == "occurrence"
    ]
    assert len(today_routines) >= 1
