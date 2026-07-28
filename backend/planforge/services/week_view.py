"""Week view assembly."""

from dataclasses import dataclass
from datetime import UTC

from planforge.domain.enums import (
    AppointmentStatus,
    TaskStatus,
    ViewItemKind,
)
from planforge.domain.local_date import LocalDate
from planforge.domain.timezone import get_timezone
from planforge.models.appointment import Appointment
from planforge.models.task import Task
from planforge.services import routine_service, weekly_target_service
from planforge.services.completion_display import completed_items_for_local_day
from planforge.services.display_date import is_item_overdue, rolled_display_date
from planforge.services.settings_service import PolicySnapshot
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class WeekItem:
    kind: ViewItemKind
    item_id: str
    title: str
    due_date: LocalDate | None
    starts_at: str | None
    ends_at: str | None
    is_overdue: bool
    routine_title: str | None = None
    is_completed: bool = False


@dataclass(frozen=True)
class WeekDayGroup:
    date: LocalDate | None
    items: list[WeekItem]
    label: str | None = None


@dataclass(frozen=True)
class WeekTargetSummary:
    target_id: str
    title: str
    completed_count: int
    target_count: int


@dataclass(frozen=True)
class WeekView:
    week_start: LocalDate
    week_end: LocalDate
    days: list[WeekDayGroup]
    targets: list[WeekTargetSummary]


def _appointment_local_date(
    appointment: Appointment,
    *,
    timezone_name: str,
) -> LocalDate:
    local = appointment.starts_at.astimezone(get_timezone(timezone_name))
    return LocalDate(local.year, local.month, local.day)


def assemble_week_view(
    *,
    session: Session,
    owner_id: str,
    week_start: LocalDate,
    today: LocalDate,
    policies: PolicySnapshot,
) -> WeekView:
    """Assemble pending items grouped by due date for a week."""
    week_end = week_start.add_days(6)
    start_date = week_start.to_date()
    end_date = week_end.to_date()

    day_map: dict[LocalDate, list[WeekItem]] = {
        week_start.add_days(offset): [] for offset in range(7)
    }
    unscheduled: list[WeekItem] = []
    upcoming: list[WeekItem] = []

    def _place_item(
        *,
        kind: ViewItemKind,
        item_id: str,
        title: str,
        due: LocalDate,
        starts_at: str | None,
        ends_at: str | None,
        routine_title: str | None = None,
    ) -> None:
        display = rolled_display_date(due=due, today=today)
        display_date = display.to_date()
        is_overdue = is_item_overdue(scheduled=due, today=today)

        if display_date > end_date:
            upcoming.append(
                WeekItem(
                    kind=kind,
                    item_id=item_id,
                    title=title,
                    due_date=due,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    is_overdue=False,
                    routine_title=routine_title,
                )
            )
        elif display_date < start_date:
            return
        elif start_date <= display_date <= end_date:
            day_map[display].append(
                WeekItem(
                    kind=kind,
                    item_id=item_id,
                    title=title,
                    due_date=due,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    is_overdue=is_overdue,
                    routine_title=routine_title,
                )
            )

    tasks = list(
        session.scalars(
            select(Task).where(
                Task.owner_id == owner_id,
                Task.status == TaskStatus.PENDING.value,
            )
        )
    )
    for task in tasks:
        if task.due_date is None:
            unscheduled.append(
                WeekItem(
                    kind=ViewItemKind.TASK,
                    item_id=task.id,
                    title=task.title,
                    due_date=None,
                    starts_at=None,
                    ends_at=None,
                    is_overdue=False,
                )
            )
            continue

        due = LocalDate.from_date(task.due_date)
        _place_item(
            kind=ViewItemKind.TASK,
            item_id=task.id,
            title=task.title,
            due=due,
            starts_at=None,
            ends_at=None,
        )

    routine_service.ensure_occurrences(
        session,
        owner_id=owner_id,
        clock_today=today,
        policies=policies,
    )
    for occurrence, routine in routine_service.list_pending_occurrences(
        session,
        owner_id=owner_id,
    ):
        scheduled = LocalDate.from_date(occurrence.scheduled_date)
        _place_item(
            kind=ViewItemKind.OCCURRENCE,
            item_id=occurrence.id,
            title=routine.title,
            due=scheduled,
            starts_at=None,
            ends_at=None,
            routine_title=routine.title,
        )

    appointments = list(
        session.scalars(
            select(Appointment).where(
                Appointment.owner_id == owner_id,
                Appointment.status == AppointmentStatus.SCHEDULED.value,
            )
        )
    )
    for appointment in appointments:
        local_date = _appointment_local_date(
            appointment,
            timezone_name=policies.timezone,
        )
        _place_item(
            kind=ViewItemKind.APPOINTMENT,
            item_id=appointment.id,
            title=appointment.title,
            due=local_date,
            starts_at=appointment.starts_at.astimezone(UTC).isoformat(),
            ends_at=appointment.ends_at.astimezone(UTC).isoformat(),
        )

    for day_items in day_map.values():
        day_items.sort(key=lambda item: item.title.lower())
    unscheduled.sort(key=lambda item: item.title.lower())
    upcoming.sort(
        key=lambda item: (
            item.due_date.to_date() if item.due_date else start_date,
            item.title.lower(),
        )
    )

    days = [
        WeekDayGroup(
            date=week_start.add_days(offset),
            items=day_map[week_start.add_days(offset)],
        )
        for offset in range(7)
    ]
    if upcoming:
        days.append(WeekDayGroup(date=None, items=upcoming, label="upcoming"))
    if unscheduled:
        days.append(WeekDayGroup(date=None, items=unscheduled, label="unscheduled"))

    if policies.week_show_completed:
        pending_ids = {
            (item.kind, item.item_id) for group in days for item in group.items
        }
        for offset in range(7):
            day = week_start.add_days(offset)
            for completed_item in completed_items_for_local_day(
                session,
                owner_id=owner_id,
                day=day,
                timezone_name=policies.timezone,
            ):
                key = (completed_item.kind, completed_item.item_id)
                if key in pending_ids:
                    continue
                pending_ids.add(key)
                day_map[day].append(
                    WeekItem(
                        kind=completed_item.kind,
                        item_id=completed_item.item_id,
                        title=completed_item.title,
                        due_date=completed_item.due_date,
                        starts_at=completed_item.starts_at,
                        ends_at=completed_item.ends_at,
                        is_overdue=False,
                        routine_title=completed_item.routine_title,
                        is_completed=True,
                    )
                )
        for day_items in day_map.values():
            day_items.sort(
                key=lambda item: (
                    1 if item.is_completed else 0,
                    item.title.lower(),
                )
            )
        days = [
            WeekDayGroup(
                date=week_start.add_days(offset),
                items=day_map[week_start.add_days(offset)],
            )
            for offset in range(7)
        ]
        if upcoming:
            days.append(WeekDayGroup(date=None, items=upcoming, label="upcoming"))
        if unscheduled:
            days.append(WeekDayGroup(date=None, items=unscheduled, label="unscheduled"))

    targets: list[WeekTargetSummary] = []
    for target in weekly_target_service.list_weekly_targets(
        session,
        owner_id=owner_id,
    ):
        completed_count, target_count = weekly_target_service.target_progress_for_week(
            session,
            owner_id=owner_id,
            target=target,
            week_start=week_start,
            week_start_day=policies.week_start_day,
        )
        targets.append(
            WeekTargetSummary(
                target_id=target.id,
                title=target.title,
                completed_count=completed_count,
                target_count=target_count,
            )
        )

    return WeekView(
        week_start=week_start,
        week_end=week_end,
        days=days,
        targets=targets,
    )
