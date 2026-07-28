"""Tests for backlog service."""

import pytest
from planforge.core.exceptions import BacklogStateError
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import BacklogStatus
from planforge.domain.local_date import LocalDate
from planforge.services import backlog_service


def test_create_backlog_item(db_session) -> None:
    item = backlog_service.create_backlog_item(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Demo backlog item",
    )
    assert item.backlog_status is BacklogStatus.ACTIVE


def test_promote_backlog_to_task(db_session) -> None:
    item = backlog_service.create_backlog_item(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Example errand",
    )
    promoted, task = backlog_service.promote_backlog_to_task(
        db_session,
        item_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        due_date=LocalDate.from_iso("2026-07-24"),
    )
    assert promoted.backlog_status is BacklogStatus.PROMOTED
    assert task.title == "Example errand"


def test_archive_non_active_raises(db_session) -> None:
    item = backlog_service.create_backlog_item(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Example errand",
    )
    backlog_service.promote_backlog_to_task(
        db_session,
        item_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        due_date=LocalDate.from_iso("2026-07-24"),
    )
    with pytest.raises(BacklogStateError):
        backlog_service.archive_backlog_item(
            db_session,
            item_id=item.id,
            owner_id=LOCAL_OWNER_ID,
        )
