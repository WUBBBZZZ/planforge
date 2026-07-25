"""Tests for task service."""

import pytest
from planforge.core.exceptions import (
    TaskNotEditableError,
    TaskStateError,
    ValidationError,
)
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import CompletionAction, TaskStatus
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
