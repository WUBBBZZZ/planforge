"""Service tests for appointments."""

from datetime import time

import pytest
from planforge.core.exceptions import (
    AppointmentDeleteError,
    AppointmentNotEditableError,
    ValidationError,
)
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import AppointmentListFilter, AppointmentStatus
from planforge.domain.local_date import LocalDate
from planforge.models.setting import Setting
from planforge.services import appointment_service

PACIFIC = "America/Los_Angeles"


def _set_timezone(session, timezone_name: str) -> None:
    session.add(Setting(owner_id=LOCAL_OWNER_ID, key="timezone", value=timezone_name))
    session.flush()


def test_create_timed_appointment(db_session) -> None:
    _set_timezone(db_session, PACIFIC)
    appointment = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Doctor",
        notes="Annual checkup",
        location="Clinic",
        category="health",
        reminder_minutes=30,
        maintenance_definition_id=None,
        is_all_day=False,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-21"),
        start_time=time(9, 0),
        end_time=time(10, 0),
        timezone_name=PACIFIC,
    )
    assert appointment.is_all_day is False
    assert appointment.starts_at is not None
    assert appointment.ends_at is not None
    assert appointment.location == "Clinic"


def test_create_all_day_multi_day_appointment(db_session) -> None:
    appointment = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Vacation",
        notes=None,
        location="Beach",
        category="travel",
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-25"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    assert appointment.is_all_day is True
    assert appointment.starts_at is None
    assert appointment.ends_at is None
    assert appointment.end_date.isoformat() == "2026-07-25"


def test_reschedule_all_day_to_timed(db_session) -> None:
    appointment = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dinner",
        notes=None,
        location=None,
        category=None,
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-21"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    updated = appointment_service.reschedule_appointment(
        db_session,
        appointment_id=appointment.id,
        owner_id=LOCAL_OWNER_ID,
        is_all_day=False,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-21"),
        start_time=time(18, 0),
        end_time=time(20, 0),
        timezone_name=PACIFIC,
    )
    assert updated.is_all_day is False
    assert updated.starts_at is not None


def test_complete_cancel_reopen_archive_restore(db_session) -> None:
    appointment = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Interview",
        notes=None,
        location=None,
        category=None,
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=False,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-21"),
        start_time=time(13, 0),
        end_time=time(14, 0),
        timezone_name=PACIFIC,
    )
    completed = appointment_service.complete_appointment(
        db_session,
        appointment_id=appointment.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert completed.appointment_status is AppointmentStatus.COMPLETED

    reopened = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Cancelled flight",
        notes=None,
        location=None,
        category=None,
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-08-01"),
        end_date=LocalDate.from_iso("2026-08-01"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    appointment_service.cancel_appointment(
        db_session,
        appointment_id=reopened.id,
        owner_id=LOCAL_OWNER_ID,
    )
    restored = appointment_service.reopen_appointment(
        db_session,
        appointment_id=reopened.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert restored.appointment_status is AppointmentStatus.SCHEDULED

    archived = appointment_service.archive_appointment(
        db_session,
        appointment_id=restored.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert archived.appointment_status is AppointmentStatus.ARCHIVED
    back = appointment_service.restore_appointment(
        db_session,
        appointment_id=archived.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert back.appointment_status is AppointmentStatus.SCHEDULED


def test_invalid_range_rejected(db_session) -> None:
    with pytest.raises(ValidationError):
        appointment_service.create_appointment(
            db_session,
            owner_id=LOCAL_OWNER_ID,
            title="Bad",
            notes=None,
            location=None,
            category=None,
            reminder_minutes=None,
            maintenance_definition_id=None,
            is_all_day=False,
            start_date=LocalDate.from_iso("2026-07-21"),
            end_date=LocalDate.from_iso("2026-07-21"),
            start_time=time(12, 0),
            end_time=time(11, 0),
            timezone_name=PACIFIC,
        )


def test_list_filters(db_session) -> None:
    today = LocalDate.from_iso("2026-07-21")
    appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Upcoming",
        notes=None,
        location=None,
        category=None,
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-07-25"),
        end_date=LocalDate.from_iso("2026-07-25"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    today_item = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Today item",
        notes=None,
        location=None,
        category=None,
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=True,
        start_date=today,
        end_date=today,
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    upcoming = appointment_service.list_appointments(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        list_filter=AppointmentListFilter.UPCOMING,
        today=today,
    )
    assert any(item.id == today_item.id for item in upcoming)
    today_list = appointment_service.list_appointments(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        list_filter=AppointmentListFilter.TODAY,
        today=today,
    )
    assert len(today_list) == 1


def test_delete_blocked_with_audit_history(db_session) -> None:
    appointment = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Delete me",
        notes=None,
        location=None,
        category=None,
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-21"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    appointment_service.complete_appointment(
        db_session,
        appointment_id=appointment.id,
        owner_id=LOCAL_OWNER_ID,
    )
    with pytest.raises(AppointmentDeleteError):
        appointment_service.delete_appointment(
            db_session,
            appointment_id=appointment.id,
            owner_id=LOCAL_OWNER_ID,
        )


def test_delete_allowed_without_history(db_session) -> None:
    appointment = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Fresh",
        notes=None,
        location=None,
        category=None,
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-21"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    appointment_id = appointment.id
    appointment_service.delete_appointment(
        db_session,
        appointment_id=appointment_id,
        owner_id=LOCAL_OWNER_ID,
    )
    remaining = appointment_service.list_appointments(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        status=AppointmentStatus.SCHEDULED,
    )
    assert all(item.id != appointment_id for item in remaining)


def test_edit_requires_scheduled_status(db_session) -> None:
    appointment = appointment_service.create_appointment(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Locked",
        notes=None,
        location=None,
        category=None,
        reminder_minutes=None,
        maintenance_definition_id=None,
        is_all_day=True,
        start_date=LocalDate.from_iso("2026-07-21"),
        end_date=LocalDate.from_iso("2026-07-21"),
        start_time=None,
        end_time=None,
        timezone_name=PACIFIC,
    )
    appointment_service.cancel_appointment(
        db_session,
        appointment_id=appointment.id,
        owner_id=LOCAL_OWNER_ID,
    )
    with pytest.raises(AppointmentNotEditableError):
        appointment_service.update_appointment(
            db_session,
            appointment_id=appointment.id,
            owner_id=LOCAL_OWNER_ID,
            title="Nope",
        )
