"""Tests for Today view assembly."""

from dataclasses import replace

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import TaskStatus, ViewItemKind
from planforge.domain.local_date import LocalDate
from planforge.models.task import Task
from planforge.services.settings_service import PolicySnapshot
from planforge.services.today_view import assemble_today_view


def _add_task(
    session,
    *,
    title: str,
    due_date: LocalDate | None,
    status: TaskStatus = TaskStatus.PENDING,
) -> Task:
    task = Task(
        owner_id=LOCAL_OWNER_ID,
        title=title,
        due_date=due_date.to_date() if due_date else None,
        status=status.value,
    )
    session.add(task)
    session.flush()
    return task


def test_due_today_not_overdue(db_session) -> None:
    ref = LocalDate.from_iso("2026-07-21")
    _add_task(db_session, title="Today task", due_date=ref)
    view = assemble_today_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=ref,
        clock_today=ref,
        policies=PolicySnapshot(),
    )
    assert len(view.items) == 1
    assert view.items[0].is_overdue is False


def test_due_today_included(db_session) -> None:
    ref = LocalDate.from_iso("2026-07-21")
    _add_task(db_session, title="Today task", due_date=ref)
    view = assemble_today_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=ref,
        clock_today=ref,
        policies=PolicySnapshot(),
    )
    assert len(view.items) == 1
    assert view.items[0].title == "Today task"
    assert view.items[0].kind is ViewItemKind.TASK
    assert view.items[0].is_overdue is False


def test_overdue_included_when_policy_true(db_session) -> None:
    ref = LocalDate.from_iso("2026-07-21")
    _add_task(
        db_session,
        title="Overdue task",
        due_date=LocalDate.from_iso("2026-07-18"),
    )
    view = assemble_today_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=ref,
        clock_today=ref,
        policies=PolicySnapshot(today_include_rolled_tasks=True),
    )
    assert len(view.items) == 1
    assert view.items[0].is_overdue is True


def test_overdue_excluded_when_policy_false(db_session) -> None:
    ref = LocalDate.from_iso("2026-07-21")
    _add_task(
        db_session,
        title="Overdue task",
        due_date=LocalDate.from_iso("2026-07-18"),
    )
    policies = replace(PolicySnapshot(), today_include_rolled_tasks=False)
    view = assemble_today_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=ref,
        clock_today=ref,
        policies=policies,
    )
    assert view.items == []


def test_unscheduled_excluded(db_session) -> None:
    ref = LocalDate.from_iso("2026-07-21")
    _add_task(db_session, title="No date", due_date=None)
    view = assemble_today_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=ref,
        clock_today=ref,
        policies=PolicySnapshot(),
    )
    assert view.items == []


def test_completed_shown_as_completed(db_session) -> None:
    ref = LocalDate.from_iso("2026-07-21")
    task = _add_task(
        db_session,
        title="Done",
        due_date=ref,
        status=TaskStatus.COMPLETED,
    )
    from datetime import UTC, datetime

    from planforge.domain.enums import CompletionAction
    from planforge.models.completion_record import CompletionRecord

    db_session.add(
        CompletionRecord(
            owner_id=LOCAL_OWNER_ID,
            entity_type="task",
            entity_id=task.id,
            action=CompletionAction.COMPLETED.value,
            recorded_at=datetime(2026, 7, 21, 15, 0, tzinfo=UTC),
        )
    )
    db_session.flush()
    view = assemble_today_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=ref,
        clock_today=ref,
        policies=PolicySnapshot(),
    )
    assert len(view.items) == 1
    assert view.items[0].is_completed is True


def test_future_day_omits_rolled_overdue_tasks(db_session) -> None:
    clock = LocalDate.from_iso("2026-07-21")
    tomorrow = LocalDate.from_iso("2026-07-22")
    _add_task(db_session, title="Still pending today", due_date=clock)

    view = assemble_today_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=tomorrow,
        clock_today=clock,
        policies=PolicySnapshot(today_include_rolled_tasks=True),
    )

    assert view.items == []
