"""Tests for weekly target service."""

from datetime import UTC, datetime

from planforge.domain.enums import CompletionAction
from planforge.models.completion_record import CompletionRecord
from planforge.services import weekly_target_service
from sqlalchemy import select

LOCAL_OWNER_ID = "local-owner"


def test_update_weekly_target_title(db_session) -> None:
    target = weekly_target_service.create_weekly_target(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Read",
        target_count=2,
    )
    updated = weekly_target_service.update_weekly_target(
        db_session,
        target_id=target.id,
        owner_id=LOCAL_OWNER_ID,
        title="Read books",
    )
    assert updated.title == "Read books"
    assert updated.target_count == 2


def test_delete_weekly_target(db_session) -> None:
    target = weekly_target_service.create_weekly_target(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Meditate",
        target_count=3,
    )
    weekly_target_service.delete_weekly_target(
        db_session,
        target_id=target.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert (
        weekly_target_service.list_weekly_targets(db_session, owner_id=LOCAL_OWNER_ID)
        == []
    )


def test_update_weekly_target_count(db_session) -> None:
    target = weekly_target_service.create_weekly_target(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Exercise",
        target_count=3,
    )
    updated = weekly_target_service.update_weekly_target(
        db_session,
        target_id=target.id,
        owner_id=LOCAL_OWNER_ID,
        target_count=5,
    )
    assert updated.target_count == 5


def test_delete_weekly_target_removes_completion_records(db_session) -> None:
    target = weekly_target_service.create_weekly_target(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Stretch",
        target_count=2,
    )
    weekly_target_service.log_target_progress(
        db_session,
        target_id=target.id,
        owner_id=LOCAL_OWNER_ID,
    )
    db_session.add(
        CompletionRecord(
            owner_id=LOCAL_OWNER_ID,
            entity_type="weekly_target",
            entity_id=target.id,
            action=CompletionAction.COMPLETED.value,
            recorded_at=datetime.now(UTC),
        )
    )
    db_session.flush()

    weekly_target_service.delete_weekly_target(
        db_session,
        target_id=target.id,
        owner_id=LOCAL_OWNER_ID,
    )
    remaining = list(
        db_session.scalars(
            select(CompletionRecord).where(
                CompletionRecord.entity_type == "weekly_target",
                CompletionRecord.entity_id == target.id,
            )
        )
    )
    assert remaining == []
