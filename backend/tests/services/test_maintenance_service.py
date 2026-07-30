"""Service tests for maintenance subsystem."""

from datetime import time

import pytest
from planforge.core.exceptions import MaintenanceLinkError
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import (
    MaintenanceIntervalUnit,
    MaintenanceNextActionStatus,
    MaintenanceStatus,
)
from planforge.domain.local_date import LocalDate
from planforge.models.setting import Setting
from planforge.services import maintenance_service

PACIFIC = "America/Los_Angeles"


def _set_timezone(session, timezone_name: str) -> None:
    session.add(Setting(owner_id=LOCAL_OWNER_ID, key="timezone", value=timezone_name))
    session.flush()


def test_create_complete_and_calculate_next_due(db_session) -> None:
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dentist",
        interval_unit=MaintenanceIntervalUnit.MONTHS,
        interval_value=6,
    )
    completed = maintenance_service.complete_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-01-31"),
    )
    assert completed.last_completed_date.isoformat() == "2026-01-31"
    assert completed.next_due_date.isoformat() == "2026-07-31"
    assert completed.next_action is MaintenanceNextActionStatus.NEEDS_SCHEDULING


def test_schedule_and_cancel_linked_appointment(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dentist",
        interval_unit=MaintenanceIntervalUnit.MONTHS,
        interval_value=6,
    )
    maintenance_service.complete_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-07-27"),
    )
    item, appointment = maintenance_service.schedule_appointment(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        title=None,
        start_date=LocalDate.from_iso("2026-10-04"),
        end_date=LocalDate.from_iso("2026-10-04"),
        is_all_day=False,
        start_time=time(9, 0),
        end_time=time(10, 0),
        timezone_name=PACIFIC,
    )
    assert item.next_action is MaintenanceNextActionStatus.SCHEDULED
    assert item.linked_appointment_id == appointment.id

    from planforge.services import appointment_service

    appointment_service.cancel_appointment(
        db_session,
        appointment_id=appointment.id,
        owner_id=LOCAL_OWNER_ID,
    )
    refreshed = maintenance_service.get_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert refreshed.linked_appointment_id is None
    assert refreshed.next_action is MaintenanceNextActionStatus.NEEDS_SCHEDULING


def test_complete_appointment_auto_completes_linked_maintenance(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dentist",
    )
    maintenance_service.complete_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-07-01"),
    )
    item, appointment = maintenance_service.schedule_appointment(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        title=None,
        start_date=LocalDate.from_iso("2026-10-04"),
        end_date=LocalDate.from_iso("2026-10-04"),
        is_all_day=True,
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    from planforge.services import appointment_service

    appointment_service.complete_appointment(
        db_session,
        appointment_id=appointment.id,
        owner_id=LOCAL_OWNER_ID,
    )
    refreshed = maintenance_service.get_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert refreshed.linked_appointment_id is None
    assert refreshed.last_completed_date.isoformat() == "2026-10-04"
    assert refreshed.next_action is MaintenanceNextActionStatus.NEEDS_SCHEDULING


def test_duplicate_linked_appointment_prevented(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    first = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dentist",
    )
    second = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Physical",
    )
    _, appointment = maintenance_service.schedule_appointment(
        db_session,
        maintenance_id=first.id,
        owner_id=LOCAL_OWNER_ID,
        title=None,
        start_date=LocalDate.from_iso("2026-10-04"),
        end_date=LocalDate.from_iso("2026-10-04"),
        is_all_day=True,
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    with pytest.raises(MaintenanceLinkError):
        maintenance_service.link_appointment(
            db_session,
            maintenance_id=second.id,
            owner_id=LOCAL_OWNER_ID,
            appointment_id=appointment.id,
        )


def test_scheduling_reminder_not_appointment(db_session) -> None:
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dentist",
    )
    maintenance_service.complete_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-07-27"),
    )
    updated = maintenance_service.set_scheduling_reminder(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        reminder_date=LocalDate.from_iso("2026-09-01"),
    )
    assert updated.next_action is MaintenanceNextActionStatus.REMINDER_SET
    assert updated.scheduling_reminder_date.isoformat() == "2026-09-01"
    assert updated.linked_appointment_id is None


def test_historical_completion_and_correction(db_session) -> None:
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Oil change",
        interval_unit=MaintenanceIntervalUnit.MONTHS,
        interval_value=3,
    )
    maintenance_service.add_historical_completion(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-03-03"),
    )
    maintenance_service.add_historical_completion(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-07-27"),
    )
    completions = maintenance_service.list_completions(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert completions[0].completed_on.isoformat() == "2026-07-27"
    assert item.last_completed_date.isoformat() == "2026-07-27"
    assert item.next_due_date.isoformat() == "2026-10-27"
    corrected = maintenance_service.correct_completion(
        db_session,
        maintenance_id=item.id,
        completion_id=completions[0].id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-07-28"),
        void_reason="Wrong day",
    )
    assert corrected.completed_on.isoformat() == "2026-07-28"
    db_session.refresh(item)
    assert item.last_completed_date.isoformat() == "2026-07-28"
    assert item.next_due_date.isoformat() == "2026-10-28"


def test_correcting_older_completion_keeps_current_schedule(db_session) -> None:
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Oil change",
        interval_unit=MaintenanceIntervalUnit.MONTHS,
        interval_value=3,
    )
    maintenance_service.add_historical_completion(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-03-03"),
    )
    maintenance_service.add_historical_completion(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-07-27"),
    )
    completions = maintenance_service.list_completions(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
    )
    older = next(
        completion
        for completion in completions
        if completion.completed_on.isoformat() == "2026-03-03"
    )
    maintenance_service.correct_completion(
        db_session,
        maintenance_id=item.id,
        completion_id=older.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-03-01"),
    )
    db_session.refresh(item)
    assert item.last_completed_date.isoformat() == "2026-07-27"
    assert item.next_due_date.isoformat() == "2026-10-27"


def test_correcting_latest_completion_clears_linked_appointment(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dentist",
        interval_unit=MaintenanceIntervalUnit.MONTHS,
        interval_value=6,
    )
    maintenance_service.complete_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-01-15"),
    )
    maintenance_service.schedule_appointment(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        title=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-07-10"),
        end_date=LocalDate.from_iso("2026-07-10"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    completions = maintenance_service.list_completions(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
    )
    maintenance_service.correct_completion(
        db_session,
        maintenance_id=item.id,
        completion_id=completions[0].id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-02-01"),
    )
    db_session.refresh(item)
    assert item.last_completed_date.isoformat() == "2026-02-01"
    assert item.next_due_date.isoformat() == "2026-08-01"
    assert item.linked_appointment_id is None
    assert item.next_action is MaintenanceNextActionStatus.NEEDS_SCHEDULING


def test_overdue_completion_uses_mark_date_not_original_due(db_session) -> None:
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Oil change",
        interval_unit=MaintenanceIntervalUnit.MONTHS,
        interval_value=3,
    )
    maintenance_service.add_historical_completion(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-04-01"),
    )
    db_session.refresh(item)
    assert item.next_due_date.isoformat() == "2026-07-01"

    completed = maintenance_service.complete_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-07-01"),
        clock_today=LocalDate.from_iso("2026-07-30"),
    )
    assert completed.last_completed_date.isoformat() == "2026-07-30"
    assert completed.next_due_date.isoformat() == "2026-10-30"


def test_overdue_appointment_completion_uses_mark_date(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dentist",
        interval_unit=MaintenanceIntervalUnit.MONTHS,
        interval_value=6,
    )
    maintenance_service.complete_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        completed_on=LocalDate.from_iso("2026-01-15"),
        clock_today=LocalDate.from_iso("2026-01-15"),
    )
    _, appointment = maintenance_service.schedule_appointment(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        title=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-07-01"),
        end_date=LocalDate.from_iso("2026-07-01"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    from planforge.services import appointment_service

    appointment_service.complete_appointment(
        db_session,
        appointment_id=appointment.id,
        owner_id=LOCAL_OWNER_ID,
        clock_today=LocalDate.from_iso("2026-07-30"),
    )
    refreshed = maintenance_service.get_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert refreshed.last_completed_date.isoformat() == "2026-07-30"
    assert refreshed.next_due_date.isoformat() == "2027-01-30"


def test_archive_restore(db_session) -> None:
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Tires",
    )
    archived = maintenance_service.archive_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert archived.maintenance_status is MaintenanceStatus.ARCHIVED
    restored = maintenance_service.restore_maintenance(
        db_session,
        maintenance_id=item.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert restored.maintenance_status is MaintenanceStatus.ACTIVE


def test_history_board_ordering(db_session) -> None:
    item = maintenance_service.create_maintenance(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Eye exam",
    )
    for day in ("2025-11-08", "2026-03-03", "2026-07-27"):
        maintenance_service.add_historical_completion(
            db_session,
            maintenance_id=item.id,
            owner_id=LOCAL_OWNER_ID,
            completed_on=LocalDate.from_iso(day),
        )
    board = maintenance_service.build_history_board(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        today=LocalDate.from_iso("2026-07-28"),
        history_limit=10,
    )
    row = next(entry for entry in board if entry["maintenance"].title == "Eye exam")
    dates = [c.completed_on.isoformat() for c in row["completions"]]
    assert dates == ["2026-07-27", "2026-03-03", "2025-11-08"]
