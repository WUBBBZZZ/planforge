"""Month view assembly."""

from dataclasses import dataclass

from planforge.domain.appointment_scheduling import appointment_times_iso
from planforge.domain.enums import (
    AppointmentStatus,
    MaintenanceStatus,
    TaskStatus,
    ViewItemKind,
)
from planforge.domain.local_date import LocalDate
from planforge.models.appointment import Appointment
from planforge.models.maintenance import MaintenanceDefinition
from planforge.models.task import Task
from planforge.services import routine_group_service, routine_service
from planforge.services.completion_display import completed_items_for_local_day
from planforge.services.display_date import is_item_overdue, rolled_display_date
from planforge.services.maintenance_display import placements_for_maintenance
from planforge.services.month_bounds import month_bounds
from planforge.services.recurring_occurrence_display import (
    list_routine_occurrences_for_calendar_window,
)
from planforge.services.settings_service import PolicySnapshot
from planforge.services.week_view import (
    WeekDayGroup,
    WeekItem,
    append_backlog_bucket,
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
    routine_service.ensure_occurrences(
        session,
        owner_id=owner_id,
        clock_today=clock_today,
        policies=policies,
        through_date=month_end,
    )
    start_date = month_start.to_date()
    end_date = month_end.to_date()
    month = f"{month_start.year:04d}-{month_start.month:02d}"

    day_count = (end_date - start_date).days + 1
    day_map: dict[LocalDate, list[WeekItem]] = {
        month_start.add_days(offset): [] for offset in range(day_count)
    }
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

    visible_routine_ids = routine_group_service.visible_routine_ids(
        session,
        owner_id=owner_id,
        view="month",
    )
    pending_routine_rows = routine_service.list_pending_occurrences(
        session,
        owner_id=owner_id,
    )
    for calendar_occurrence in list_routine_occurrences_for_calendar_window(
        pending_routine_rows,
        today=clock_today,
        window_start=month_start,
        window_end=month_end,
        missed_behavior=policies.routine_missed_behavior,
    ):
        if calendar_occurrence.routine.id not in visible_routine_ids:
            continue
        day_map[calendar_occurrence.display].append(
            WeekItem(
                kind=ViewItemKind.OCCURRENCE,
                item_id=calendar_occurrence.occurrence.id,
                title=calendar_occurrence.routine.title,
                due_date=calendar_occurrence.scheduled,
                starts_at=None,
                ends_at=None,
                is_overdue=calendar_occurrence.is_overdue,
                routine_title=calendar_occurrence.routine.title,
                occurrence_role=(
                    "overdue" if calendar_occurrence.is_overdue else None
                ),
            )
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
        placed_in_month = False
        for day, item in week_items_for_appointment(
            appointment,
            timezone_name=policies.timezone,
            window_start=month_start,
            window_end=month_end,
        ):
            placed_in_month = True
            day_map[day].append(item)
        if not placed_in_month:
            start = LocalDate.from_date(appointment.start_date)
            starts_at, ends_at = appointment_times_iso(
                is_all_day=appointment.is_all_day,
                starts_at=appointment.starts_at,
                ends_at=appointment.ends_at,
            )
            if start.to_date() > end_date:
                upcoming.append(
                    WeekItem(
                        kind=ViewItemKind.APPOINTMENT,
                        item_id=appointment.id,
                        title=appointment.title,
                        due_date=start,
                        starts_at=starts_at,
                        ends_at=ends_at,
                        is_overdue=False,
                        is_all_day=appointment.is_all_day,
                        span_start_date=start,
                        span_end_date=LocalDate.from_date(appointment.end_date),
                        span_segment="single",
                        location=appointment.location,
                        status=appointment.status,
                    )
                )

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
        for placement in placements_for_maintenance(
            maintenance,
            period_start=month_start,
            period_end=month_end,
            clock_today=clock_today,
            view="month",
        ):
            if placement.target == "upcoming":
                upcoming.append(
                    WeekItem(
                        kind=placement.kind,
                        item_id=placement.item_id,
                        title=placement.title,
                        due_date=placement.due_date,
                        starts_at=None,
                        ends_at=None,
                        is_overdue=placement.is_overdue,
                    )
                )
            elif placement.display_date is not None:
                day_map[placement.display_date].append(
                    WeekItem(
                        kind=placement.kind,
                        item_id=placement.item_id,
                        title=placement.title,
                        due_date=placement.due_date,
                        starts_at=None,
                        ends_at=None,
                        is_overdue=placement.is_overdue,
                    )
                )

    for day_items in day_map.values():
        day_items.sort(key=lambda item: item.title.lower())
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

    days = append_backlog_bucket(
        session,
        owner_id=owner_id,
        days=days,
    )

    return MonthView(
        month=month,
        month_start=month_start,
        month_end=month_end,
        week_start_day=policies.week_start_day,
        days=days,
    )
