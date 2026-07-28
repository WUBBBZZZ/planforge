"""Tests for Month view assembly."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import ViewItemKind
from planforge.domain.local_date import LocalDate
from planforge.models.task import Task
from planforge.services.month_bounds import month_bounds
from planforge.services.month_view import assemble_month_view
from planforge.services.settings_service import PolicySnapshot


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


def test_month_bounds() -> None:
    ref = LocalDate.from_iso("2026-07-15")
    start, end = month_bounds(reference_date=ref)
    assert start.to_iso() == "2026-07-01"
    assert end.to_iso() == "2026-07-31"


def test_tasks_grouped_by_due_date(db_session) -> None:
    reference = LocalDate.from_iso("2026-07-01")
    _add_task(db_session, title="Early July", due_date=reference.add_days(2))
    _add_task(db_session, title="Late July", due_date=reference.add_days(30))

    view = assemble_month_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=reference,
        clock_today=reference,
        policies=PolicySnapshot(),
    )

    assert view.month == "2026-07"
    assert len(view.days) == 31
    assert view.days[2].items[0].title == "Early July"
    assert view.days[30].items[0].title == "Late July"
    assert view.days[2].items[0].kind is ViewItemKind.TASK


def test_upcoming_bucket(db_session) -> None:
    reference = LocalDate.from_iso("2026-07-01")
    _add_task(db_session, title="August task", due_date=LocalDate.from_iso("2026-08-05"))

    view = assemble_month_view(
        session=db_session,
        owner_id=LOCAL_OWNER_ID,
        reference_date=reference,
        clock_today=reference,
        policies=PolicySnapshot(),
    )

    upcoming = view.days[-1]
    assert upcoming.label == "upcoming"
    assert upcoming.items[0].title == "August task"
