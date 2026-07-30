"""Week view assembly."""

from dataclasses import dataclass

from planforge.domain.appointment_scheduling import (
    appointment_overlaps_day,
    appointment_times_iso,
    local_dates_for_schedule,
    span_segment_for_day,
)
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
from planforge.services import backlog_service, routine_group_service, routine_service, weekly_target_service
from planforge.services.maintenance_display import placements_for_maintenance
from planforge.services.completion_display import completed_items_for_local_day
from planforge.services.display_date import is_item_overdue, rolled_display_date
from planforge.services.recurring_occurrence_display import (
    list_routine_occurrences_for_calendar_window,
)
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
    occurrence_role: str | None = None
    is_all_day: bool = False
    span_start_date: LocalDate | None = None
    span_end_date: LocalDate | None = None
    span_segment: str | None = None
    location: str | None = None
    status: str | None = None


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
    routine_service.ensure_occurrences(
        session,
        owner_id=owner_id,
        clock_today=today,
        policies=policies,
        through_date=week_end,
    )
    start_date = week_start.to_date()
    end_date = week_end.to_date()

    day_map: dict[LocalDate, list[WeekItem]] = {
        week_start.add_days(offset): [] for offset in range(7)
    }
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
        is_overdue: bool | None = None,
        occurrence_role: str | None = None,
    ) -> None:
        display = rolled_display_date(due=due, today=today)
        display_date = display.to_date()
        resolved_overdue = (
            is_overdue
            if is_overdue is not None
            else is_item_overdue(scheduled=due, today=today)
        )

        if display_date > end_date:
            if due > today.add_days(90):
                return
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
                    occurrence_role=occurrence_role,
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
                    is_overdue=resolved_overdue,
                    routine_title=routine_title,
                    occurrence_role=occurrence_role,
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

    visible_routine_ids = routine_group_service.visible_routine_ids(
        session,
        owner_id=owner_id,
        view="week",
    )
    pending_routine_rows = routine_service.list_pending_occurrences(
        session,
        owner_id=owner_id,
    )
    for calendar_occurrence in list_routine_occurrences_for_calendar_window(
        pending_routine_rows,
        today=today,
        window_start=week_start,
        window_end=week_end,
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
            period_start=week_start,
            period_end=week_end,
            clock_today=today,
            view="week",
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

    appointments = list(
        session.scalars(
            select(Appointment).where(
                Appointment.owner_id == owner_id,
                Appointment.status == AppointmentStatus.SCHEDULED.value,
            )
        )
    )
    for appointment in appointments:
        placed = False
        for day, item in week_items_for_appointment(
            appointment,
            timezone_name=policies.timezone,
            window_start=week_start,
            window_end=week_end,
        ):
            placed = True
            display = rolled_display_date(due=day, today=today)
            display_date = display.to_date()
            if display_date > end_date:
                upcoming.append(item)
            elif start_date <= display_date <= end_date:
                day_map[display].append(item)
        if not placed:
            start = LocalDate.from_date(appointment.start_date)
            if start.to_date() <= end_date:
                continue
            starts_at, ends_at = appointment_times_iso(
                is_all_day=appointment.is_all_day,
                starts_at=appointment.starts_at,
                ends_at=appointment.ends_at,
            )
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
            date=week_start.add_days(offset),
            items=day_map[week_start.add_days(offset)],
        )
        for offset in range(7)
    ]
    if upcoming:
        days.append(WeekDayGroup(date=None, items=upcoming, label="upcoming"))

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
                        is_all_day=completed_item.is_all_day,
                        span_start_date=completed_item.span_start_date,
                        span_end_date=completed_item.span_end_date,
                        span_segment=completed_item.span_segment,
                        location=completed_item.location,
                        status=completed_item.status,
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
            timezone_name=policies.timezone,
        )
        targets.append(
            WeekTargetSummary(
                target_id=target.id,
                title=target.title,
                completed_count=completed_count,
                target_count=target_count,
            )
        )

    days = append_backlog_bucket(
        session,
        owner_id=owner_id,
        days=days,
    )

    return WeekView(
        week_start=week_start,
        week_end=week_end,
        days=days,
        targets=targets,
    )


def append_backlog_bucket(
    session: Session,
    *,
    owner_id: str,
    days: list[WeekDayGroup],
) -> list[WeekDayGroup]:
    """Append active backlog items as a dedicated bucket."""
    backlog_items = backlog_service.list_backlog_items(session, owner_id=owner_id)
    if not backlog_items:
        return days
    bucket_items = [
        WeekItem(
            kind=ViewItemKind.BACKLOG,
            item_id=item.id,
            title=item.title,
            due_date=None,
            starts_at=None,
            ends_at=None,
            is_overdue=False,
        )
        for item in backlog_items
    ]
    return [*days, WeekDayGroup(date=None, items=bucket_items, label="backlog")]


def week_items_for_appointment(
    appointment: Appointment,
    *,
    timezone_name: str,
    window_start: LocalDate,
    window_end: LocalDate,
) -> list[tuple[LocalDate, WeekItem]]:
    """Build week/month items for each local day an appointment occupies."""
    start_date = LocalDate.from_date(appointment.start_date)
    end_date = LocalDate.from_date(appointment.end_date)
    starts_at, ends_at = appointment_times_iso(
        is_all_day=appointment.is_all_day,
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
    )
    items: list[tuple[LocalDate, WeekItem]] = []
    for day in local_dates_for_schedule(
        is_all_day=appointment.is_all_day,
        start_date=start_date,
        end_date=end_date,
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
        timezone_name=timezone_name,
    ):
        if (
            day.to_date() < window_start.to_date()
            or day.to_date() > window_end.to_date()
        ):
            continue
        if not appointment_overlaps_day(
            is_all_day=appointment.is_all_day,
            start_date=appointment.start_date,
            end_date=appointment.end_date,
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            day=day,
            timezone_name=timezone_name,
        ):
            continue
        segment = span_segment_for_day(day, start_date=start_date, end_date=end_date)
        items.append(
            (
                day,
                WeekItem(
                    kind=ViewItemKind.APPOINTMENT,
                    item_id=appointment.id,
                    title=appointment.title,
                    due_date=day,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    is_overdue=False,
                    is_all_day=appointment.is_all_day,
                    span_start_date=start_date,
                    span_end_date=end_date,
                    span_segment=segment.value,
                    location=appointment.location,
                    status=appointment.status,
                ),
            )
        )
    return items
