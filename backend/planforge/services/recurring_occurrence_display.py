"""Select which routine occurrences appear in planner views."""

from dataclasses import dataclass

from planforge.domain.local_date import LocalDate
from planforge.domain.recurring_display import (
    DEFAULT_RECURRING_DISPLAY_POLICY,
    OccurrenceDisplayRole,
    RecurringDisplayPolicy,
)
from planforge.models.occurrence import Occurrence
from planforge.models.routine import Routine
from planforge.services.display_date import is_item_overdue, rolled_display_date


@dataclass(frozen=True)
class VisibleRoutineOccurrence:
    """Routine occurrence selected for planner display."""

    occurrence: Occurrence
    routine: Routine
    scheduled: LocalDate
    is_overdue: bool
    role: OccurrenceDisplayRole


@dataclass(frozen=True)
class CalendarRoutineOccurrence:
    """Routine occurrence placed on a calendar day within a view window."""

    occurrence: Occurrence
    routine: Routine
    scheduled: LocalDate
    display: LocalDate
    is_overdue: bool


def list_routine_occurrences_for_calendar_window(
    rows: list[tuple[Occurrence, Routine]],
    *,
    today: LocalDate,
    window_start: LocalDate,
    window_end: LocalDate,
    missed_behavior: str = "prompt",
) -> list[CalendarRoutineOccurrence]:
    """Return routine occurrences whose rolled display date falls in the view window."""
    include_overdue = missed_behavior in {"prompt", "roll_forward"}
    items: list[CalendarRoutineOccurrence] = []
    for occurrence, routine in rows:
        scheduled = LocalDate.from_date(occurrence.scheduled_date)
        is_overdue = is_item_overdue(scheduled=scheduled, today=today)
        if is_overdue and not include_overdue:
            continue
        display = rolled_display_date(due=scheduled, today=today)
        if display < window_start or display > window_end:
            continue
        items.append(
            CalendarRoutineOccurrence(
                occurrence=occurrence,
                routine=routine,
                scheduled=scheduled,
                display=display,
                is_overdue=is_overdue,
            )
        )
    items.sort(key=lambda item: (item.display, item.routine.title.lower()))
    return items


def select_visible_routine_occurrences(
    rows: list[tuple[Occurrence, Routine]],
    *,
    today: LocalDate,
    horizon_start: LocalDate,
    horizon_end: LocalDate,
    policy: RecurringDisplayPolicy = DEFAULT_RECURRING_DISPLAY_POLICY,
    missed_behavior: str = "prompt",
) -> list[VisibleRoutineOccurrence]:
    """Return the pending occurrences that should appear for each routine."""
    grouped: dict[str, list[tuple[Occurrence, Routine, LocalDate]]] = {}
    for occurrence, routine in rows:
        scheduled = LocalDate.from_date(occurrence.scheduled_date)
        if scheduled > horizon_end:
            continue
        grouped.setdefault(routine.id, []).append((occurrence, routine, scheduled))

    visible: list[VisibleRoutineOccurrence] = []
    include_overdue = missed_behavior in {"prompt", "roll_forward"}

    for members in grouped.values():
        members.sort(key=lambda item: item[2])
        selected = _select_for_routine(
            members,
            today=today,
            horizon_start=horizon_start,
            include_overdue=include_overdue,
            max_following=policy.max_following_occurrences(),
        )
        visible.extend(selected)

    visible.sort(key=lambda item: (item.scheduled, item.routine.title.lower()))
    return visible


def _select_for_routine(
    members: list[tuple[Occurrence, Routine, LocalDate]],
    *,
    today: LocalDate,
    horizon_start: LocalDate,
    include_overdue: bool,
    max_following: int,
) -> list[VisibleRoutineOccurrence]:
    overdue: VisibleRoutineOccurrence | None = None
    pending_current: list[tuple[Occurrence, Routine, LocalDate]] = []

    for occurrence, routine, scheduled in members:
        if is_item_overdue(scheduled=scheduled, today=today):
            if include_overdue and overdue is None:
                overdue = VisibleRoutineOccurrence(
                    occurrence=occurrence,
                    routine=routine,
                    scheduled=scheduled,
                    is_overdue=True,
                    role=OccurrenceDisplayRole.OVERDUE,
                )
            continue
        if scheduled < horizon_start:
            continue
        pending_current.append((occurrence, routine, scheduled))

    selected: list[VisibleRoutineOccurrence] = []
    if overdue is not None:
        selected.append(overdue)

    if not pending_current:
        return selected

    current_occurrence, current_routine, current_scheduled = pending_current[0]
    selected.append(
        VisibleRoutineOccurrence(
            occurrence=current_occurrence,
            routine=current_routine,
            scheduled=current_scheduled,
            is_overdue=False,
            role=OccurrenceDisplayRole.CURRENT,
        )
    )

    if max_following > 0 and len(pending_current) > 1:
        next_occurrence, next_routine, next_scheduled = pending_current[1]
        selected.append(
            VisibleRoutineOccurrence(
                occurrence=next_occurrence,
                routine=next_routine,
                scheduled=next_scheduled,
                is_overdue=False,
                role=OccurrenceDisplayRole.NEXT,
            )
        )

    return selected
