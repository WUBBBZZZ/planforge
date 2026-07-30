"""Packing list business logic."""

from __future__ import annotations

from planforge.core.exceptions import PackingListNotFoundError, ValidationError
from planforge.domain.enums import PackingEntryType, PackingQuestionAnswer
from planforge.models.packing_list import PackingList, PackingListEntry
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload


def _get_list_or_raise(
    session: Session,
    *,
    list_id: str,
    owner_id: str,
) -> PackingList:
    packing_list = session.scalar(
        select(PackingList).where(
            PackingList.id == list_id,
            PackingList.owner_id == owner_id,
        )
    )
    if packing_list is None:
        raise PackingListNotFoundError(f"Packing list not found: {list_id}")
    return packing_list


def _get_entry_or_raise(
    session: Session,
    *,
    entry_id: str,
    owner_id: str,
) -> PackingListEntry:
    entry = session.scalar(
        select(PackingListEntry).where(
            PackingListEntry.id == entry_id,
            PackingListEntry.owner_id == owner_id,
        )
    )
    if entry is None:
        raise PackingListNotFoundError(f"Packing list entry not found: {entry_id}")
    return entry


def list_packing_lists(session: Session, *, owner_id: str) -> list[PackingList]:
    lists = list(
        session.scalars(
            select(PackingList)
            .where(PackingList.owner_id == owner_id)
            .options(selectinload(PackingList.entries))
            .order_by(PackingList.sort_order, PackingList.title)
        )
    )
    for packing_list in lists:
        packing_list.entries.sort(
            key=lambda entry: (entry.sort_order, entry.title.lower())
        )
    return lists


def get_packing_list(
    session: Session,
    *,
    list_id: str,
    owner_id: str,
) -> PackingList:
    packing_list = session.scalar(
        select(PackingList)
        .where(PackingList.id == list_id, PackingList.owner_id == owner_id)
        .options(selectinload(PackingList.entries))
    )
    if packing_list is None:
        raise PackingListNotFoundError(f"Packing list not found: {list_id}")
    packing_list.entries.sort(key=lambda entry: (entry.sort_order, entry.title.lower()))
    return packing_list


def create_packing_list(
    session: Session,
    *,
    owner_id: str,
    title: str,
    notes: str | None = None,
) -> PackingList:
    cleaned = title.strip()
    if not cleaned:
        raise ValidationError("List title must not be empty")
    max_sort = session.scalar(
        select(func.max(PackingList.sort_order)).where(PackingList.owner_id == owner_id)
    )
    packing_list = PackingList(
        owner_id=owner_id,
        title=cleaned,
        notes=notes.strip() if notes else None,
        sort_order=(max_sort or -1) + 1,
    )
    session.add(packing_list)
    session.flush()
    return packing_list


def update_packing_list(
    session: Session,
    *,
    list_id: str,
    owner_id: str,
    title: str | None = None,
    notes: str | None = None,
) -> PackingList:
    packing_list = _get_list_or_raise(session, list_id=list_id, owner_id=owner_id)
    if title is not None:
        cleaned = title.strip()
        if not cleaned:
            raise ValidationError("List title must not be empty")
        packing_list.title = cleaned
    if notes is not None:
        packing_list.notes = notes.strip() if notes else None
    session.flush()
    return get_packing_list(session, list_id=list_id, owner_id=owner_id)


def delete_packing_list(session: Session, *, list_id: str, owner_id: str) -> None:
    packing_list = _get_list_or_raise(session, list_id=list_id, owner_id=owner_id)
    session.delete(packing_list)
    session.flush()


def create_entry(
    session: Session,
    *,
    list_id: str,
    owner_id: str,
    entry_type: PackingEntryType,
    title: str,
) -> PackingListEntry:
    _get_list_or_raise(session, list_id=list_id, owner_id=owner_id)
    cleaned = title.strip()
    if not cleaned:
        raise ValidationError("Entry title must not be empty")

    max_sort = session.scalar(
        select(func.max(PackingListEntry.sort_order)).where(
            PackingListEntry.list_id == list_id,
            PackingListEntry.entry_type == entry_type.value,
        )
    )
    entry = PackingListEntry(
        list_id=list_id,
        owner_id=owner_id,
        entry_type=entry_type.value,
        title=cleaned,
        sort_order=(max_sort or -1) + 1,
        is_checked=False,
        answer=None,
    )
    session.add(entry)
    session.flush()
    return entry


def update_entry(
    session: Session,
    *,
    entry_id: str,
    owner_id: str,
    title: str | None = None,
    is_checked: bool | None = None,
    answer: PackingQuestionAnswer | None = None,
    clear_answer: bool = False,
) -> PackingListEntry:
    entry = _get_entry_or_raise(session, entry_id=entry_id, owner_id=owner_id)
    if title is not None:
        cleaned = title.strip()
        if not cleaned:
            raise ValidationError("Entry title must not be empty")
        entry.title = cleaned
    if entry.packing_entry_type is PackingEntryType.ITEM:
        if is_checked is not None:
            entry.is_checked = is_checked
        if answer is not None or clear_answer:
            raise ValidationError("Answers apply to questions only")
    else:
        if is_checked is not None:
            raise ValidationError("Use answer yes/no for questions")
        if clear_answer:
            entry.answer = None
        elif answer is not None:
            entry.answer = answer.value
    session.flush()
    return entry


def delete_entry(session: Session, *, entry_id: str, owner_id: str) -> None:
    entry = _get_entry_or_raise(session, entry_id=entry_id, owner_id=owner_id)
    session.delete(entry)
    session.flush()
