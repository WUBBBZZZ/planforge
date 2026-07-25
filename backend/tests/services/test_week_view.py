"""Tests for Week view assembly."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.core.policy_defaults import PolicySnapshot
from planforge.domain.local_date import LocalDate
from planforge.models.task import Task
from planforge.services.week_view import assemble_week_view, week_bounds


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
    ref = LocalDate.from_iso("2026-07-23")  # Thursday
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
        policies=PolicySnapshot(),
    )

    monday_tasks = view.days[0].tasks
    wednesday_tasks = view.days[2].tasks
    assert [task.title for task in monday_tasks] == ["Monday task"]
    assert [task.title for task in wednesday_tasks] == ["Wednesday task"]


def test_unscheduled_bucket(db_session) -> None:
    week_start = LocalDate.from_iso("2026-07-20")
    _add_task(db_session, title="Someday", due_date=None)

    view = assemble_week_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        week_start=week_start,
        policies=PolicySnapshot(),
    )

    unscheduled = view.days[-1]
    assert unscheduled.date is None
    assert len(unscheduled.tasks) == 1
    assert unscheduled.tasks[0].title == "Someday"
