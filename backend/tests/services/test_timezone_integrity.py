"""Timezone bucketing and planner-clock integration tests."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.appointment_scheduling import local_date_from_instant
from planforge.domain.enums import CompletionAction
from planforge.domain.local_date import LocalDate
from planforge.models.appointment import Appointment
from planforge.models.completion_record import CompletionRecord
from planforge.models.setting import Setting
from planforge.services import weekly_target_service
from planforge.services.completion_display import list_completed_records_for_local_day
from planforge.services.settings_service import PolicySnapshot, update_setting
from planforge.services.week_bounds import week_bounds

PACIFIC = "America/Los_Angeles"
EASTERN = "America/New_York"


def _set_timezone(session, timezone_name: str) -> None:
    session.add(Setting(owner_id=LOCAL_OWNER_ID, key="timezone", value=timezone_name))
    session.flush()


def test_completion_buckets_by_planner_timezone_not_utc(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    day = LocalDate.from_iso("2026-07-21")
    # 2026-07-21 06:30 UTC is still 2026-07-20 23:30 in Los Angeles.
    recorded_at = datetime(2026, 7, 21, 6, 30, tzinfo=UTC)
    db_session.add(
        CompletionRecord(
            owner_id=LOCAL_OWNER_ID,
            entity_type="task",
            entity_id="task-1",
            action=CompletionAction.COMPLETED.value,
            recorded_at=recorded_at,
        )
    )
    db_session.flush()

    july_20 = list_completed_records_for_local_day(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        day=LocalDate.from_iso("2026-07-20"),
        timezone_name=PACIFIC,
    )
    july_21 = list_completed_records_for_local_day(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        day=day,
        timezone_name=PACIFIC,
    )
    assert len(july_20) == 1
    assert july_21 == []


def test_completion_near_local_midnight_eastern(db_session) -> None:
    _set_timezone(db_session, EASTERN)
    # 2026-03-09 04:30 UTC = 2026-03-09 00:30 EDT (after spring-forward gap).
    recorded_at = datetime(2026, 3, 9, 4, 30, tzinfo=UTC)
    db_session.add(
        CompletionRecord(
            owner_id=LOCAL_OWNER_ID,
            entity_type="task",
            entity_id="task-dst",
            action=CompletionAction.COMPLETED.value,
            recorded_at=recorded_at,
        )
    )
    db_session.flush()

    records = list_completed_records_for_local_day(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        day=LocalDate.from_iso("2026-03-09"),
        timezone_name=EASTERN,
    )
    assert len(records) == 1


def test_appointment_buckets_by_planner_timezone(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    # 2026-07-21 07:00 UTC = 2026-07-21 00:00 PDT.
    appointment = Appointment(
        owner_id=LOCAL_OWNER_ID,
        title="Late night",
        is_all_day=False,
        start_date=datetime(2026, 7, 21, 7, 0, tzinfo=UTC).date(),
        end_date=datetime(2026, 7, 21, 8, 0, tzinfo=UTC).date(),
        starts_at=datetime(2026, 7, 21, 7, 0, tzinfo=UTC),
        ends_at=datetime(2026, 7, 21, 8, 0, tzinfo=UTC),
        status="scheduled",
    )
    db_session.add(appointment)
    db_session.flush()

    local_day = local_date_from_instant(appointment.starts_at, timezone_name=PACIFIC)
    assert local_day.to_iso() == "2026-07-21"

    # One hour earlier UTC is still the previous local day.
    appointment.starts_at = datetime(2026, 7, 21, 6, 30, tzinfo=UTC)
    appointment.ends_at = datetime(2026, 7, 21, 7, 30, tzinfo=UTC)
    local_day = local_date_from_instant(appointment.starts_at, timezone_name=PACIFIC)
    assert local_day.to_iso() == "2026-07-20"


def test_weekly_target_progress_uses_local_week_bounds(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    target = weekly_target_service.create_weekly_target(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Walk",
        target_count=3,
    )
    week_start, _ = week_bounds(
        reference_date=LocalDate.from_iso("2026-07-22"),
        week_start_day="sunday",
    )
    assert week_start.to_iso() == "2026-07-19"
    # Still Saturday evening in Pacific for the week that starts Sunday.
    db_session.add(
        CompletionRecord(
            owner_id=LOCAL_OWNER_ID,
            entity_type="weekly_target",
            entity_id=target.id,
            action=CompletionAction.COMPLETED.value,
            recorded_at=datetime(2026, 7, 19, 6, 0, tzinfo=UTC),
        )
    )
    db_session.flush()

    completed, target_count = weekly_target_service.target_progress_for_week(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        target=target,
        week_start=week_start,
        week_start_day="sunday",
        timezone_name=PACIFIC,
    )
    assert target_count == 3
    assert completed == 0

    db_session.add(
        CompletionRecord(
            owner_id=LOCAL_OWNER_ID,
            entity_type="weekly_target",
            entity_id=target.id,
            action=CompletionAction.COMPLETED.value,
            recorded_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
        )
    )
    db_session.flush()
    completed, _ = weekly_target_service.target_progress_for_week(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        target=target,
        week_start=week_start,
        week_start_day="sunday",
        timezone_name=PACIFIC,
    )
    assert completed == 1


def test_saturday_week_start_boundaries() -> None:
    ref = LocalDate.from_iso("2026-07-22")
    week_start, week_end = week_bounds(reference_date=ref, week_start_day="saturday")
    assert week_start.to_iso() == "2026-07-18"
    assert week_end.to_iso() == "2026-07-24"


def test_changing_timezone_shifts_completion_day(db_session) -> None:
    recorded_at = datetime(2026, 7, 21, 6, 30, tzinfo=UTC)
    db_session.add(
        CompletionRecord(
            owner_id=LOCAL_OWNER_ID,
            entity_type="task",
            entity_id="task-shift",
            action=CompletionAction.COMPLETED.value,
            recorded_at=recorded_at,
        )
    )
    db_session.flush()

    pacific_records = list_completed_records_for_local_day(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        day=LocalDate.from_iso("2026-07-20"),
        timezone_name=PACIFIC,
    )
    utc_records = list_completed_records_for_local_day(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        day=LocalDate.from_iso("2026-07-21"),
        timezone_name="UTC",
    )
    assert len(pacific_records) == 1
    assert len(utc_records) == 1

    update_setting(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        key="timezone",
        value=PACIFIC,
    )
    policies = PolicySnapshot(timezone=PACIFIC)
    assert policies.timezone == PACIFIC


def test_dst_fall_back_completion_stays_on_local_day(db_session) -> None:
    # 2026-11-01 05:30 UTC = 2026-11-01 01:30 EDT (before fall-back ends).
    recorded_at = datetime(2026, 11, 1, 5, 30, tzinfo=UTC)
    db_session.add(
        CompletionRecord(
            owner_id=LOCAL_OWNER_ID,
            entity_type="task",
            entity_id="task-fallback",
            action=CompletionAction.COMPLETED.value,
            recorded_at=recorded_at,
        )
    )
    db_session.flush()

    records = list_completed_records_for_local_day(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        day=LocalDate.from_iso("2026-11-01"),
        timezone_name=EASTERN,
    )
    assert len(records) == 1
    local = recorded_at.astimezone(ZoneInfo(EASTERN))
    assert local.day == 1
