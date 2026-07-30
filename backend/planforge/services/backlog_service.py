"""Backlog business logic."""

from planforge.core.exceptions import (
    BacklogNotFoundError,
    BacklogStateError,
    ValidationError,
)
from planforge.domain.enums import BacklogStatus
from planforge.domain.local_date import LocalDate
from planforge.models.backlog_item import BacklogItem
from planforge.models.task import Task
from planforge.services import task_service
from sqlalchemy import select
from sqlalchemy.orm import Session


def _get_backlog_or_raise(
    session: Session,
    *,
    item_id: str,
    owner_id: str,
) -> BacklogItem:
    item = session.scalar(
        select(BacklogItem).where(
            BacklogItem.id == item_id,
            BacklogItem.owner_id == owner_id,
        )
    )
    if item is None:
        raise BacklogNotFoundError(f"Backlog item not found: {item_id}")
    return item


def create_backlog_item(
    session: Session,
    *,
    owner_id: str,
    title: str,
    notes: str | None = None,
) -> BacklogItem:
    """Create an active backlog item."""
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValidationError("Title must not be empty")

    item = BacklogItem(
        owner_id=owner_id,
        title=cleaned_title,
        notes=notes,
        status=BacklogStatus.ACTIVE.value,
    )
    session.add(item)
    session.flush()
    return item


def list_backlog_items(
    session: Session,
    *,
    owner_id: str,
    status: BacklogStatus | None = BacklogStatus.ACTIVE,
) -> list[BacklogItem]:
    """List backlog items for an owner."""
    query = select(BacklogItem).where(BacklogItem.owner_id == owner_id)
    if status is not None:
        query = query.where(BacklogItem.status == status.value)
    query = query.order_by(BacklogItem.title)
    return list(session.scalars(query))


def archive_backlog_item(
    session: Session,
    *,
    item_id: str,
    owner_id: str,
) -> BacklogItem:
    """Archive an active backlog item."""
    item = _get_backlog_or_raise(session, item_id=item_id, owner_id=owner_id)
    if item.backlog_status is not BacklogStatus.ACTIVE:
        raise BacklogStateError("Only active backlog items can be archived")
    item.status = BacklogStatus.ARCHIVED.value
    session.flush()
    return item


def delete_backlog_item(session: Session, *, item_id: str, owner_id: str) -> None:
    """Permanently delete a backlog item."""
    item = _get_backlog_or_raise(session, item_id=item_id, owner_id=owner_id)
    if item.backlog_status is BacklogStatus.PROMOTED:
        raise BacklogStateError("Promoted backlog items cannot be deleted")
    session.delete(item)
    session.flush()


def promote_backlog_to_task(
    session: Session,
    *,
    item_id: str,
    owner_id: str,
    due_date: LocalDate,
) -> tuple[BacklogItem, Task]:
    """Promote a backlog item to a dated task."""
    item = _get_backlog_or_raise(session, item_id=item_id, owner_id=owner_id)
    if item.backlog_status is not BacklogStatus.ACTIVE:
        raise BacklogStateError("Only active backlog items can be promoted")

    task = task_service.create_task(
        session,
        owner_id=owner_id,
        title=item.title,
        notes=item.notes,
        due_date=due_date,
    )
    item.status = BacklogStatus.PROMOTED.value
    item.promoted_entity_type = "task"
    item.promoted_entity_id = task.id
    session.flush()
    return item, task
