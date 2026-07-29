"""Month view assembly."""

from dataclasses import dataclass

from planforge.domain.enums import (
    AppointmentStatus,
    MaintenanceStatus,
    TaskStatus,
    ViewItemKind,
)
from planforge.domain.local_date import LocalDate
from planforge.domain.recurring_display import DEFAULT_RECURRING_DISPLAY_POLICY
from planforge.models.appointment import Appointment
from planforge.models.maintenance import MaintenanceDefinition
from planforge.models.task import Task
from planforge.services import routine_service
from planforge.services.completion_display import completed_items_for_local_day
from planforge.services.display_date import rolled_display_date
from planforge.services.month_bounds import month_bounds
from planforge.services.recurring_occurrence_display import (
    select_visible_routine_occurrences,
)
from planforge.services.settings_service import PolicySnapshot
from planforge.services.week_view import (
    WeekDayGroup,
    WeekItem,
    week_items_for_appointment,
)
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class MonthView:
    month: str
    month_start: LocalDate
    month_end: LocalDate
    week_start_day: str
    days: list[WeekDayGroup]


def assemble_month_view(
    *,
    session: Session,
    owner_id: str,
    reference_date: LocalDate,
    clock_today: LocalDate,
    policies: PolicySnapshot,
) -> MonthView:
    """Assemble pending items grouped by due date for a calendar month."""
    month_start, month_end = month_bounds(reference_date=reference_date)
    start_date = month_start.to_date()
    end_date = month_end.to_date()
    month = f"{month_start.year:04d}-{month_start.month:02d}"

    day_count = (end_date - start_date).days + 1
    day_map: dict[LocalDate, list[WeekItem]] = {
        month_start.add_days(offset): [] for offset in range(day_count)
    }
    unscheduled: list[WeekItem] = []
    upcoming: list[WeekItem] = []

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
        due_date = due.to_date()
        if start_date <= due_date <= end_date:
            day_map[due].append(
                WeekItem(
                    kind=ViewItemKind.TASK,
                    item_id=task.id,
                    title=task.title,
                    due_date=due,
                    starts_at=None,
                    ends_at=None,
                    is_overdue=False,
                )
            )
        elif due_date > end_date:
            upcoming.append(
                WeekItem(
                    kind=ViewItemKind.TASK,
                    item_id=task.id,
                    title=task.title,
                    due_date=due,
                    starts_at=None,
                    ends_at=None,
                    is_overdue=False,
                )
            )

    recurring_policy = DEFAULT_RECURRING_DISPLAY_POLICY
    horizon_start, horizon_end = recurring_policy.horizon_bounds(
        today=clock_today,
        week_start_day=policies.week_start_day,
    )
    for visible in select_visible_routine_occurrences(
        routine_service.list_pending_occurrences(session, owner_id=owner_id),
        today=clock_today,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        policy=recurring_policy,
        missed_behavior=policies.routine_missed_behavior,
    ):
        scheduled = visible.scheduled
        display = rolled_display_date(due=scheduled, today=clock_today)
        due_date = display.to_date()
        item = WeekItem(
            kind=ViewItemKind.OCCURRENCE,
            item_id=visible.occurrence.id,
            title=visible.routine.title,
            due_date=scheduled,
            starts_at=None,
            ends_at=None,
            is_overdue=visible.is_overdue,
            routine_title=visible.routine.title,
            occurrence_role=visible.role.value,
        )
        if start_date <= due_date <= end_date:
            day_map[display].append(item)
        elif due_date > end_date:
            upcoming.append(item)

    appointments = list(
        session.scalars(
            select(Appointment).where(
                Appointment.owner_id == owner_id,
                Appointment.status == AppointmentStatus.SCHEDULED.value,
            )
        )
    )
    for appointment in appointments:
        for day, item in week_items_for_appointment(
            appointment,
            timezone_name=policies.timezone,
            window_start=month_start,
            window_end=month_end,
        ):
            day_map[day].append(item)

    maintenance_items = list(
        session.scalars(
            select(MaintenanceDefinition).where(
                MaintenanceDefinition.owner_id == owner_id,
                MaintenanceDefinition.status == MaintenanceStatus.ACTIVE.value,
                MaintenanceDefinition.next_due_date.is_not(None),
            )
        )
    )
    for maintenance in maintenance_items:
        assert maintenance.next_due_date is not None
        due = LocalDate.from_date(maintenance.next_due_date)
        due_date = due.to_date()
        if start_date <= due_date <= end_date:
            day_map[due].append(
                WeekItem(
                    kind=ViewItemKind.MAINTENANCE,
                    item_id=maintenance.id,
                    title=maintenance.title,
                    due_date=due,
                    starts_at=None,
                    ends_at=None,
                    is_overdue=False,
                )
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
            date=month_start.add_days(offset),
            items=day_map[month_start.add_days(offset)],
        )
        for offset in range(day_count)
    ]
    if upcoming:
        days.append(WeekDayGroup(date=None, items=upcoming, label="upcoming"))
    if unscheduled:
        days.append(WeekDayGroup(date=None, items=unscheduled, label="unscheduled"))

    if policies.week_show_completed:
        pending_ids = {
            (item.kind, item.item_id) for group in days for item in group.items
        }
        for offset in range(day_count):
            day = month_start.add_days(offset)
            for completed in completed_items_for_local_day(
                session,
                owner_id=owner_id,
                day=day,
                timezone_name=policies.timezone,
            ):
                key = (completed.kind, completed.item_id)
                if key in pending_ids:
                    continue
                pending_ids.add(key)
                day_map[day].append(
                    WeekItem(
                        kind=completed.kind,
                        item_id=completed.item_id,
                        title=completed.title,
                        due_date=completed.due_date,
                        starts_at=completed.starts_at,
                        ends_at=completed.ends_at,
                        is_overdue=False,
                        routine_title=completed.routine_title,
                        is_completed=True,
                        is_all_day=completed.is_all_day,
                        span_start_date=completed.span_start_date,
                        span_end_date=completed.span_end_date,
                        span_segment=completed.span_segment,
                        location=completed.location,
                        status=completed.status,
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
                date=month_start.add_days(offset),
                items=day_map[month_start.add_days(offset)],
            )
            for offset in range(day_count)
        ]
        if upcoming:
            days.append(WeekDayGroup(date=None, items=upcoming, label="upcoming"))
        if unscheduled:
            days.append(WeekDayGroup(date=None, items=unscheduled, label="unscheduled"))

    return MonthView(
        month=month,
        month_start=month_start,
        month_end=month_end,
        week_start_day=policies.week_start_day,
        days=days,
    )
