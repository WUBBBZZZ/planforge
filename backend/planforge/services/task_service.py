"""Task business logic."""

from datetime import UTC, datetime
from typing import Any

from planforge.core.exceptions import (
    TaskNotEditableError,
    TaskNotFoundError,
    TaskStateError,
    ValidationError,
)
from planforge.domain.enums import CompletionAction, TaskStatus
from planforge.domain.local_date import LocalDate
from planforge.models.completion_record import CompletionRecord
from planforge.models.task import Task
from sqlalchemy import select
from sqlalchemy.orm import Session

_UNSET: Any = object()
UNSET = _UNSET


def _get_task_or_raise(session: Session, *, task_id: str, owner_id: str) -> Task:
    task = session.scalar(
        select(Task).where(Task.id == task_id, Task.owner_id == owner_id)
    )
    if task is None:
        raise TaskNotFoundError(f"Task not found: {task_id}")
    return task


def _append_completion_record(
    session: Session,
    *,
    owner_id: str,
    task_id: str,
    action: CompletionAction,
) -> None:
    session.add(
        CompletionRecord(
            owner_id=owner_id,
            entity_type="task",
            entity_id=task_id,
            action=action.value,
            recorded_at=datetime.now(UTC),
        )
    )


def create_task(
    session: Session,
    *,
    owner_id: str,
    title: str,
    notes: str | None = None,
    due_date: LocalDate | None = None,
) -> Task:
    """Create a pending task."""
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValidationError("Title must not be empty")

    task = Task(
        owner_id=owner_id,
        title=cleaned_title,
        notes=notes,
        due_date=due_date.to_date() if due_date else None,
        status=TaskStatus.PENDING.value,
    )
    session.add(task)
    session.flush()
    return task


def list_tasks(
    session: Session,
    *,
    owner_id: str,
    status: TaskStatus | None = None,
) -> list[Task]:
    """List tasks for an owner, optionally filtered by status."""
    query = select(Task).where(Task.owner_id == owner_id).order_by(Task.title)
    if status is not None:
        query = query.where(Task.status == status.value)
    return list(session.scalars(query))


def get_task(session: Session, *, task_id: str, owner_id: str) -> Task:
    """Return a single task or raise TaskNotFoundError."""
    return _get_task_or_raise(session, task_id=task_id, owner_id=owner_id)


def update_task(
    session: Session,
    *,
    task_id: str,
    owner_id: str,
    title: str | None = None,
    notes: str | None = None,
    due_date: LocalDate | None | Any = _UNSET,
) -> Task:
    """Update a pending task."""
    task = _get_task_or_raise(session, task_id=task_id, owner_id=owner_id)
    if task.task_status is not TaskStatus.PENDING:
        raise TaskNotEditableError("Only pending tasks can be edited")

    if title is not None:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValidationError("Title must not be empty")
        task.title = cleaned_title

    if notes is not None:
        task.notes = notes

    if due_date is not _UNSET:
        task.due_date = due_date.to_date() if due_date is not None else None

    session.flush()
    return task


def complete_task(session: Session, *, task_id: str, owner_id: str) -> Task:
    """Mark a task completed and append a completion record."""
    task = _get_task_or_raise(session, task_id=task_id, owner_id=owner_id)
    if task.task_status is TaskStatus.COMPLETED:
        raise TaskStateError("Task is already completed", status=TaskStatus.COMPLETED)
    if task.task_status is TaskStatus.CANCELLED:
        raise TaskStateError(
            "Cancelled tasks cannot be completed", status=TaskStatus.CANCELLED
        )

    task.status = TaskStatus.COMPLETED.value
    _append_completion_record(
        session,
        owner_id=owner_id,
        task_id=task.id,
        action=CompletionAction.COMPLETED,
    )
    session.flush()
    return task


def cancel_task(session: Session, *, task_id: str, owner_id: str) -> Task:
    """Mark a task cancelled and append a completion record."""
    task = _get_task_or_raise(session, task_id=task_id, owner_id=owner_id)
    if task.task_status is TaskStatus.CANCELLED:
        raise TaskStateError("Task is already cancelled", status=TaskStatus.CANCELLED)
    if task.task_status is TaskStatus.COMPLETED:
        raise TaskStateError(
            "Completed tasks cannot be cancelled", status=TaskStatus.COMPLETED
        )

    task.status = TaskStatus.CANCELLED.value
    _append_completion_record(
        session,
        owner_id=owner_id,
        task_id=task.id,
        action=CompletionAction.CANCELLED,
    )
    session.flush()
    return task
