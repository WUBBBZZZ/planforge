"""Tests for Week view assembly."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import ViewItemKind
from planforge.domain.local_date import LocalDate
from planforge.models.task import Task
from planforge.services.settings_service import PolicySnapshot
from planforge.services.week_bounds import week_bounds
from planforge.services.week_view import assemble_week_view


def _add_task(session, *, title: str, due_date: LocalDate | None) -> Task:
    task = Task(
        owner_id=LOCAL_OWNER_ID,
        title=title,
        due_date=due_date.to_date() if due_date else None,
        status="pending",
    )
    session.add(task)
    session.flush()
    return task


def test_week_bounds_monday_default() -> None:
    ref = LocalDate.from_iso("2026-07-23")
    start, end = week_bounds(reference_date=ref, week_start_day="monday")
    assert start.to_iso() == "2026-07-20"
    assert end.to_iso() == "2026-07-26"


def test_tasks_grouped_by_due_date(db_session) -> None:
    week_start = LocalDate.from_iso("2026-07-20")
    _add_task(db_session, title="Monday task", due_date=week_start)
    _add_task(db_session, title="Wednesday task", due_date=week_start.add_days(2))

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=week_start,
        policies=PolicySnapshot(),
    )

    monday_items = view.days[0].items
    wednesday_items = view.days[2].items
    assert [item.title for item in monday_items] == ["Monday task"]
    assert [item.title for item in wednesday_items] == ["Wednesday task"]
    assert monday_items[0].kind is ViewItemKind.TASK


def test_undated_tasks_omitted_from_week_view(db_session) -> None:
    week_start = LocalDate.from_iso("2026-07-20")
    _add_task(db_session, title="Someday", due_date=None)

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=week_start,
        policies=PolicySnapshot(),
    )

    assert all(group.label != "unscheduled" for group in view.days)
    assert all(item.title != "Someday" for group in view.days for item in group.items)


def test_upcoming_bucket(db_session) -> None:
    week_start = LocalDate.from_iso("2026-07-20")
    _add_task(db_session, title="Next week", due_date=week_start.add_days(7))
    _add_task(db_session, title="Later", due_date=week_start.add_days(10))

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=week_start,
        policies=PolicySnapshot(),
    )

    upcoming = view.days[-1]
    assert upcoming.date is None
    assert upcoming.label == "upcoming"
    assert [item.title for item in upcoming.items] == ["Next week", "Later"]


def test_backlog_bucket(db_session) -> None:
    from planforge.services import backlog_service

    week_start = LocalDate.from_iso("2026-07-20")
    backlog_service.create_backlog_item(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Someday idea",
    )

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=week_start,
        policies=PolicySnapshot(),
    )

    backlog = view.days[-1]
    assert backlog.date is None
    assert backlog.label == "backlog"
    assert [item.title for item in backlog.items] == ["Someday idea"]
    assert backlog.items[0].kind is ViewItemKind.BACKLOG


def test_due_today_not_overdue_in_week_view(db_session) -> None:
    today = LocalDate.from_iso("2026-07-26")
    week_start = LocalDate.from_iso("2026-07-20")
    _add_task(db_session, title="Saturday task", due_date=today)

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=PolicySnapshot(),
    )

    saturday_items = view.days[6].items
    assert [item.title for item in saturday_items] == ["Saturday task"]
    assert saturday_items[0].is_overdue is False


def test_overdue_task_rolls_to_today(db_session) -> None:
    week_start = LocalDate.from_iso("2026-07-20")
    today = LocalDate.from_iso("2026-07-26")
    _add_task(db_session, title="Missed Monday", due_date=week_start)

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=PolicySnapshot(),
    )

    saturday_items = view.days[6].items
    assert [item.title for item in saturday_items] == ["Missed Monday"]
    assert saturday_items[0].is_overdue is True
    assert view.days[0].items == []


def test_overdue_task_hidden_in_future_week(db_session) -> None:
    week_start = LocalDate.from_iso("2026-07-27")
    today = LocalDate.from_iso("2026-07-26")
    _add_task(
        db_session, title="Missed Monday", due_date=LocalDate.from_iso("2026-07-20")
    )

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        today=today,
        policies=PolicySnapshot(),
    )

    assert all(group.items == [] for group in view.days[:7])


def test_past_appointments_omitted_from_upcoming(db_session) -> None:
    from datetime import UTC, datetime

    from planforge.models.appointment import Appointment

    week_start = LocalDate.from_iso("2026-07-27")
    today = LocalDate.from_iso("2026-07-30")
    db_session.add(
        Appointment(
            owner_id=LOCAL_OWNER_ID,
            title="Past dentist",
            is_all_day=True,
            start_date=datetime(2026, 7, 1, 0, 0, tzinfo=UTC).date(),
            end_date=datetime(2026, 7, 1, 0, 0, tzinfo=UTC).date(),
            starts_at=datetime(2026, 7, 1, 0, 0, tzinfo=UTC),
            ends_at=datetime(2026, 7, 1, 0, 0, tzinfo=UTC),
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

    upcoming = next((group for group in view.days if group.label == "upcoming"), None)
    if upcoming is not None:
        assert all(item.title != "Past dentist" for item in upcoming.items)
