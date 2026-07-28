"""Tests for task service."""

import pytest
from planforge.core.exceptions import (
    TaskNotEditableError,
    TaskStateError,
    ValidationError,
)
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import CompletionAction, TaskStatus
from planforge.domain.local_date import LocalDate
from planforge.models.completion_record import CompletionRecord
from planforge.services import task_service
from sqlalchemy import select


def test_create_trims_title(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="  Water plants  ",
    )
    assert task.title == "Water plants"


def test_empty_title_raises(db_session) -> None:
    with pytest.raises(ValidationError):
        task_service.create_task(
            db_session,
            owner_id=LOCAL_OWNER_ID,
            title="   ",
        )


def test_complete_pending_creates_record(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Demo task",
    )
    completed = task_service.complete_task(
        db_session,
        task_id=task.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert completed.task_status is TaskStatus.COMPLETED

    records = list(
        db_session.scalars(
            select(CompletionRecord).where(CompletionRecord.entity_id == task.id)
        )
    )
    assert len(records) == 1
    assert records[0].action == CompletionAction.COMPLETED.value


def test_complete_twice_raises(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Demo task",
    )
    task_service.complete_task(db_session, task_id=task.id, owner_id=LOCAL_OWNER_ID)
    with pytest.raises(TaskStateError):
        task_service.complete_task(db_session, task_id=task.id, owner_id=LOCAL_OWNER_ID)


def test_cancel_pending_creates_record(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Demo task",
    )
    cancelled = task_service.cancel_task(
        db_session,
        task_id=task.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert cancelled.task_status is TaskStatus.CANCELLED

    records = list(
        db_session.scalars(
            select(CompletionRecord).where(CompletionRecord.entity_id == task.id)
        )
    )
    assert len(records) == 1
    assert records[0].action == CompletionAction.CANCELLED.value


def test_update_completed_raises(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Demo task",
    )
    task_service.complete_task(db_session, task_id=task.id, owner_id=LOCAL_OWNER_ID)
    with pytest.raises(TaskNotEditableError):
        task_service.update_task(
            db_session,
            task_id=task.id,
            owner_id=LOCAL_OWNER_ID,
            title="New title",
        )


def test_reopen_completed_restores_pending_and_preserves_due_date(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Demo task",
        due_date=LocalDate.from_iso("2026-07-21"),
    )
    task_service.complete_task(db_session, task_id=task.id, owner_id=LOCAL_OWNER_ID)
    reopened = task_service.reopen_task(
        db_session,
        task_id=task.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert reopened.task_status is TaskStatus.PENDING
    assert reopened.due_date.isoformat() == "2026-07-21"

    records = list(
        db_session.scalars(
            select(CompletionRecord).where(CompletionRecord.entity_id == task.id)
        )
    )
    assert len(records) == 2
    assert {record.action for record in records} == {
        CompletionAction.COMPLETED.value,
        CompletionAction.REOPENED.value,
    }


def test_reopen_cancelled_restores_pending(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Demo task",
    )
    task_service.cancel_task(db_session, task_id=task.id, owner_id=LOCAL_OWNER_ID)
    reopened = task_service.reopen_task(
        db_session,
        task_id=task.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert reopened.task_status is TaskStatus.PENDING


def test_reopen_pending_raises(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Demo task",
    )
    with pytest.raises(TaskStateError):
        task_service.reopen_task(
            db_session,
            task_id=task.id,
            owner_id=LOCAL_OWNER_ID,
        )


def test_move_pending_task_creates_backlog_with_provenance(db_session) -> None:
    from planforge.models.backlog_item import BacklogItem

    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Schedule later",
        notes="Some notes",
        due_date=LocalDate.from_iso("2026-07-21"),
    )
    moved_task, backlog_item = task_service.move_task_to_backlog(
        db_session,
        task_id=task.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert moved_task.task_status is TaskStatus.MOVED_TO_BACKLOG
    assert moved_task.due_date is None
    assert backlog_item.title == "Schedule later"
    assert backlog_item.notes == "Some notes"
    assert backlog_item.source_entity_type == "task"
    assert backlog_item.source_entity_id == task.id

    records = list(
        db_session.scalars(
            select(CompletionRecord).where(CompletionRecord.entity_id == task.id)
        )
    )
    assert len(records) == 1
    assert records[0].action == CompletionAction.MOVED_TO_BACKLOG.value

    stored_backlog = db_session.get(BacklogItem, backlog_item.id)
    assert stored_backlog is not None
    assert stored_backlog.backlog_status.value == "active"


def test_move_task_is_idempotent(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Schedule later",
        due_date=LocalDate.from_iso("2026-07-21"),
    )
    _, first_backlog = task_service.move_task_to_backlog(
        db_session,
        task_id=task.id,
        owner_id=LOCAL_OWNER_ID,
    )
    _, second_backlog = task_service.move_task_to_backlog(
        db_session,
        task_id=task.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert first_backlog.id == second_backlog.id


def test_move_completed_task_raises(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Done task",
    )
    task_service.complete_task(db_session, task_id=task.id, owner_id=LOCAL_OWNER_ID)
    with pytest.raises(TaskStateError):
        task_service.move_task_to_backlog(
            db_session,
            task_id=task.id,
            owner_id=LOCAL_OWNER_ID,
        )


def test_move_cancelled_task_raises(db_session) -> None:
    task = task_service.create_task(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Cancelled task",
    )
    task_service.cancel_task(db_session, task_id=task.id, owner_id=LOCAL_OWNER_ID)
    with pytest.raises(TaskStateError):
        task_service.move_task_to_backlog(
            db_session,
            task_id=task.id,
            owner_id=LOCAL_OWNER_ID,
        )
