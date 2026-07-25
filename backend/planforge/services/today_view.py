"""Today view assembly."""

from dataclasses import dataclass

from planforge.core.policy_defaults import PolicySnapshot
from planforge.domain.enums import TaskStatus
from planforge.domain.local_date import LocalDate
from planforge.models.task import Task
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class TodayTaskItem:
    task_id: str
    title: str
    notes: str | None
    due_date: LocalDate | None
    is_overdue: bool


@dataclass(frozen=True)
class TodayView:
    reference_date: LocalDate
    tasks: list[TodayTaskItem]


def assemble_today_view(
    *,
    session: Session,
    owner_id: str,
    reference_date: LocalDate,
    policies: PolicySnapshot,
) -> TodayView:
    """Assemble pending tasks for the Today view."""
    ref = reference_date.to_date()
    tasks = list(
        session.scalars(
            select(Task).where(
                Task.owner_id == owner_id,
                Task.status == TaskStatus.PENDING.value,
                Task.due_date.is_not(None),
            )
        )
    )

    items: list[TodayTaskItem] = []
    for task in tasks:
        assert task.due_date is not None
        due = LocalDate.from_date(task.due_date)
        if due.to_date() == ref:
            items.append(
                TodayTaskItem(
                    task_id=task.id,
                    title=task.title,
                    notes=task.notes,
                    due_date=due,
                    is_overdue=False,
                )
            )
        elif policies.today_include_rolled_tasks and due.to_date() < ref:
            items.append(
                TodayTaskItem(
                    task_id=task.id,
                    title=task.title,
                    notes=task.notes,
                    due_date=due,
                    is_overdue=True,
                )
            )

    items.sort(
        key=lambda item: (
            0 if item.is_overdue else 1,
            item.due_date.to_iso() if item.due_date else "",
            item.title.lower(),
        )
    )
    return TodayView(reference_date=reference_date, tasks=items)
