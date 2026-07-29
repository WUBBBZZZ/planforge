"""SQLite UTCDateTime round-trip regression tests."""

from datetime import UTC, datetime

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.datetime_utils import as_utc_aware
from planforge.domain.enums import CompletionAction
from planforge.models.completion_record import CompletionRecord


def test_sqlite_loads_completion_record_as_utc_aware(db_session) -> None:
    recorded_at = datetime(2026, 7, 21, 15, 30, tzinfo=UTC)
    record = CompletionRecord(
        owner_id=LOCAL_OWNER_ID,
        entity_type="task",
        entity_id="task-utc",
        action=CompletionAction.COMPLETED.value,
        recorded_at=recorded_at,
    )
    db_session.add(record)
    db_session.flush()
    db_session.expire(record)

    loaded = db_session.get(CompletionRecord, record.id)
    assert loaded is not None
    aware = as_utc_aware(loaded.recorded_at)
    assert aware.tzinfo is UTC
    assert aware == recorded_at
