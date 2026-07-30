"""Routine group business logic."""

from __future__ import annotations

from typing import Literal

from planforge.core.exceptions import (
    RoutineGroupNotFoundError,
    RoutineNotFoundError,
    ValidationError,
)
from planforge.models.routine import Routine
from planforge.models.routine_group import RoutineGroup
from sqlalchemy import func, select
from sqlalchemy.orm import Session

MISC_GROUP_NAME = "Misc"


def _get_group_or_raise(
    session: Session,
    *,
    group_id: str,
    owner_id: str,
) -> RoutineGroup:
    group = session.scalar(
        select(RoutineGroup).where(
            RoutineGroup.id == group_id,
            RoutineGroup.owner_id == owner_id,
        )
    )
    if group is None:
        raise RoutineGroupNotFoundError(f"Routine group not found: {group_id}")
    return group


def get_misc_group(session: Session, *, owner_id: str) -> RoutineGroup:
    """Return the system Misc group, creating it when missing."""
    group = session.scalar(
        select(RoutineGroup).where(
            RoutineGroup.owner_id == owner_id,
            RoutineGroup.is_system.is_(True),
        )
    )
    if group is not None:
        return group

    max_sort = session.scalar(
        select(func.max(RoutineGroup.sort_order)).where(
            RoutineGroup.owner_id == owner_id
        )
    )
    group = RoutineGroup(
        owner_id=owner_id,
        name=MISC_GROUP_NAME,
        sort_order=(max_sort or -1) + 1,
        week_visible=False,
        month_visible=False,
        is_system=True,
    )
    session.add(group)
    session.flush()
    return group


def ensure_default_groups(session: Session, *, owner_id: str) -> RoutineGroup:
    """Ensure the Misc group exists and routines without a group are assigned."""
    misc = get_misc_group(session, owner_id=owner_id)
    orphans = list(
        session.scalars(
            select(Routine).where(
                Routine.owner_id == owner_id,
                Routine.group_id.is_(None),
            )
        )
    )
    for index, routine in enumerate(orphans):
        routine.group_id = misc.id
        routine.sort_order = index
    if orphans:
        session.flush()
    return misc


def visible_routine_ids(
    session: Session,
    *,
    owner_id: str,
    view: Literal["week", "month"] = "week",
) -> set[str]:
    """Return routine IDs whose group is visible on a planner calendar view."""
    visibility_column = (
        RoutineGroup.week_visible if view == "week" else RoutineGroup.month_visible
    )
    rows = session.execute(
        select(Routine.id)
        .join(RoutineGroup, RoutineGroup.id == Routine.group_id)
        .where(
            Routine.owner_id == owner_id,
            RoutineGroup.owner_id == owner_id,
            visibility_column.is_(True),
        )
    )
    return {row[0] for row in rows}


def list_groups(session: Session, *, owner_id: str) -> list[RoutineGroup]:
    """List groups in display order."""
    ensure_default_groups(session, owner_id=owner_id)
    return list(
        session.scalars(
            select(RoutineGroup)
            .where(RoutineGroup.owner_id == owner_id)
            .order_by(RoutineGroup.sort_order, RoutineGroup.name)
        )
    )


def list_grouped_routines(
    session: Session,
    *,
    owner_id: str,
) -> list[tuple[RoutineGroup, list[Routine]]]:
    """Return groups with routines ordered within each group."""
    ensure_default_groups(session, owner_id=owner_id)
    groups = list_groups(session, owner_id=owner_id)
    routines = list(
        session.scalars(
            select(Routine)
            .where(Routine.owner_id == owner_id)
            .order_by(Routine.sort_order, Routine.title)
        )
    )
    by_group: dict[str, list[Routine]] = {group.id: [] for group in groups}
    misc = next(group for group in groups if group.is_system)
    for routine in routines:
        bucket = by_group.get(routine.group_id or "", None)
        if bucket is None:
            routine.group_id = misc.id
            bucket = by_group[misc.id]
        bucket.append(routine)
    return [(group, by_group[group.id]) for group in groups]


def create_group(session: Session, *, owner_id: str, name: str) -> RoutineGroup:
    cleaned = name.strip()
    if not cleaned:
        raise ValidationError("Group name must not be empty")
    if cleaned.casefold() == MISC_GROUP_NAME.casefold():
        raise ValidationError(f'"{MISC_GROUP_NAME}" is reserved for the default group')

    existing = session.scalar(
        select(RoutineGroup).where(
            RoutineGroup.owner_id == owner_id,
            func.lower(RoutineGroup.name) == cleaned.lower(),
        )
    )
    if existing is not None:
        raise ValidationError("A group with this name already exists")

    max_sort = session.scalar(
        select(func.max(RoutineGroup.sort_order)).where(
            RoutineGroup.owner_id == owner_id
        )
    )
    group = RoutineGroup(
        owner_id=owner_id,
        name=cleaned,
        sort_order=(max_sort or -1) + 1,
        week_visible=False,
        month_visible=False,
        is_system=False,
    )
    session.add(group)
    session.flush()
    return group


def update_group(
    session: Session,
    *,
    group_id: str,
    owner_id: str,
    name: str | None = None,
    week_visible: bool | None = None,
    month_visible: bool | None = None,
) -> RoutineGroup:
    group = _get_group_or_raise(session, group_id=group_id, owner_id=owner_id)
    if name is not None:
        cleaned = name.strip()
        if not cleaned:
            raise ValidationError("Group name must not be empty")
        if group.is_system and cleaned != MISC_GROUP_NAME:
            raise ValidationError("The Misc group cannot be renamed")
        if not group.is_system and cleaned.casefold() == MISC_GROUP_NAME.casefold():
            raise ValidationError(f'"{MISC_GROUP_NAME}" is reserved for the default group')
        group.name = cleaned
    if week_visible is not None:
        group.week_visible = week_visible
    if month_visible is not None:
        group.month_visible = month_visible
    session.flush()
    return group


def delete_group(session: Session, *, group_id: str, owner_id: str) -> None:
    group = _get_group_or_raise(session, group_id=group_id, owner_id=owner_id)
    if group.is_system:
        raise ValidationError("The Misc group cannot be deleted")
    misc = get_misc_group(session, owner_id=owner_id)
    routines = list(
        session.scalars(select(Routine).where(Routine.group_id == group.id))
    )
    next_sort = session.scalar(
        select(func.max(Routine.sort_order)).where(Routine.group_id == misc.id)
    )
    base_sort = (next_sort or -1) + 1
    for offset, routine in enumerate(routines):
        routine.group_id = misc.id
        routine.sort_order = base_sort + offset
    session.flush()
    session.delete(group)
    session.flush()


def reorder_groups(
    session: Session,
    *,
    owner_id: str,
    ordered_group_ids: list[str],
) -> list[RoutineGroup]:
    groups = list_groups(session, owner_id=owner_id)
    known_ids = {group.id for group in groups}
    if set(ordered_group_ids) != known_ids:
        raise ValidationError("Group reorder must include every group exactly once")
    order_map = {group_id: index for index, group_id in enumerate(ordered_group_ids)}
    for group in groups:
        group.sort_order = order_map[group.id]
    session.flush()
    return list_groups(session, owner_id=owner_id)


def move_routine(
    session: Session,
    *,
    owner_id: str,
    routine_id: str,
    group_id: str,
    sort_order: int,
) -> Routine:
    if sort_order < 0:
        raise ValidationError("sort_order must be zero or positive")
    _get_group_or_raise(session, group_id=group_id, owner_id=owner_id)
    routine = session.scalar(
        select(Routine).where(
            Routine.id == routine_id,
            Routine.owner_id == owner_id,
        )
    )
    if routine is None:
        raise RoutineNotFoundError(f"Routine not found: {routine_id}")

    previous_group_id = routine.group_id
    routine.group_id = group_id
    routine.sort_order = sort_order

    siblings = list(
        session.scalars(
            select(Routine)
            .where(
                Routine.owner_id == owner_id,
                Routine.group_id == group_id,
                Routine.id != routine_id,
            )
            .order_by(Routine.sort_order, Routine.title)
        )
    )
    for index, sibling in enumerate(siblings):
        target = index if index < sort_order else index + 1
        sibling.sort_order = target

    if previous_group_id and previous_group_id != group_id:
        old_siblings = list(
            session.scalars(
                select(Routine)
                .where(
                    Routine.owner_id == owner_id,
                    Routine.group_id == previous_group_id,
                )
                .order_by(Routine.sort_order, Routine.title)
            )
        )
        for index, sibling in enumerate(old_siblings):
            sibling.sort_order = index

    session.flush()
    return routine


def reorder_routines_in_group(
    session: Session,
    *,
    owner_id: str,
    group_id: str,
    ordered_routine_ids: list[str],
) -> list[Routine]:
    _get_group_or_raise(session, group_id=group_id, owner_id=owner_id)
    routines = list(
        session.scalars(
            select(Routine).where(
                Routine.owner_id == owner_id,
                Routine.group_id == group_id,
            )
        )
    )
    known_ids = {routine.id for routine in routines}
    if set(ordered_routine_ids) != known_ids:
        raise ValidationError(
            "Routine reorder must include every routine in the group exactly once"
        )
    order_map = {
        routine_id: index for index, routine_id in enumerate(ordered_routine_ids)
    }
    for routine in routines:
        routine.sort_order = order_map[routine.id]
    session.flush()
    return list(
        session.scalars(
            select(Routine)
            .where(Routine.group_id == group_id, Routine.owner_id == owner_id)
            .order_by(Routine.sort_order, Routine.title)
        )
    )
