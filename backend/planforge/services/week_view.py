"""Week view assembly."""

from dataclasses import dataclass
from datetime import timedelta

from planforge.core.policy_defaults import PolicySnapshot
from planforge.domain.enums import TaskStatus
from planforge.domain.local_date import LocalDate
from planforge.models.task import Task
from sqlalchemy import select
from sqlalchemy.orm import Session

_WEEKDAY_BY_NAME = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


@dataclass(frozen=True)
class WeekTaskItem:
    task_id: str
    title: str
    due_date: LocalDate | None
    is_overdue: bool


@dataclass(frozen=True)
class WeekDayGroup:
    date: LocalDate | None
    tasks: list[WeekTaskItem]


@dataclass(frozen=True)
class WeekView:
    week_start: LocalDate
    week_end: LocalDate
    days: list[WeekDayGroup]


def week_bounds(
    *,
    reference_date: LocalDate,
    week_start_day: str,
) -> tuple[LocalDate, LocalDate]:
    """Return inclusive week start and end dates for the reference date."""
    start_weekday = _WEEKDAY_BY_NAME[week_start_day]
    current = reference_date.to_date()
    delta_days = (current.weekday() - start_weekday) % 7
    week_start = current - timedelta(days=delta_days)
    week_end = week_start + timedelta(days=6)
    return LocalDate.from_date(week_start), LocalDate.from_date(week_end)


def assemble_week_view(
    *,
    session: Session,
    owner_id: str,
    week_start: LocalDate,
    policies: PolicySnapshot,
) -> WeekView:
    """Assemble pending tasks grouped by due date for a week."""
    week_end = week_start.add_days(6)
    start_date = week_start.to_date()
    end_date = week_end.to_date()

    tasks = list(
        session.scalars(
            select(Task).where(
                Task.owner_id == owner_id,
                Task.status == TaskStatus.PENDING.value,
            )
        )
    )

    day_map: dict[LocalDate, list[WeekTaskItem]] = {
        week_start.add_days(offset): [] for offset in range(7)
    }
    unscheduled: list[WeekTaskItem] = []

    for task in tasks:
        if task.due_date is None:
            unscheduled.append(
                WeekTaskItem(
                    task_id=task.id,
                    title=task.title,
                    due_date=None,
                    is_overdue=False,
                )
            )
            continue

        due = LocalDate.from_date(task.due_date)
        due_date = due.to_date()

        if policies.week_include_overdue_tasks and due_date < start_date:
            day_map[week_start].append(
                WeekTaskItem(
                    task_id=task.id,
                    title=task.title,
                    due_date=due,
                    is_overdue=True,
                )
            )
        elif start_date <= due_date <= end_date:
            day_map[due].append(
                WeekTaskItem(
                    task_id=task.id,
                    title=task.title,
                    due_date=due,
                    is_overdue=False,
                )
            )

    for day_tasks in day_map.values():
        day_tasks.sort(key=lambda item: item.title.lower())
    unscheduled.sort(key=lambda item: item.title.lower())

    days = [
        WeekDayGroup(
            date=week_start.add_days(offset), tasks=day_map[week_start.add_days(offset)]
        )
        for offset in range(7)
    ]
    days.append(WeekDayGroup(date=None, tasks=unscheduled))

    return WeekView(week_start=week_start, week_end=week_end, days=days)
