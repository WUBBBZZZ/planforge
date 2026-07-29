"""Occurrence uniqueness and generation integrity tests."""

from datetime import date

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import OccurrenceStatus
from planforge.domain.local_date import LocalDate
from planforge.models.occurrence import Occurrence
from planforge.services import routine_service
from planforge.services.settings_service import PolicySnapshot
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker


def test_repeated_generation_does_not_create_duplicates(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Daily",
        days_of_week=[0, 1, 2, 3, 4],
        clock_today=today,
    )
    policies = PolicySnapshot(routine_horizon_days=14)
    for _ in range(3):
        routine_service.ensure_occurrences(
            db_session,
            owner_id=LOCAL_OWNER_ID,
            clock_today=today,
            policies=policies,
        )

    count = db_session.scalar(
        select(func.count())
        .select_from(Occurrence)
        .where(Occurrence.owner_id == LOCAL_OWNER_ID)
    )
    pending = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )
    assert count == len(pending)
    dates = {occurrence.scheduled_date for occurrence, _ in pending}
    assert len(dates) == len(pending)


def test_concurrent_generation_keeps_single_occurrence(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Thursday",
        days_of_week=[3],
        clock_today=today,
    )
    db_session.commit()

    bind = db_session.get_bind()
    factory = sessionmaker(bind=bind)

    def _generate_in_fresh_session() -> None:
        session = factory()
        try:
            routine_service.ensure_occurrences(
                session,
                owner_id=LOCAL_OWNER_ID,
                clock_today=today,
                policies=PolicySnapshot(routine_horizon_days=14),
            )
            session.commit()
        finally:
            session.close()

    _generate_in_fresh_session()
    _generate_in_fresh_session()

    count = db_session.scalar(
        select(func.count())
        .select_from(Occurrence)
        .where(
            Occurrence.routine_id == routine.id,
            Occurrence.scheduled_date == date(2026, 7, 23),
        )
    )
    assert count == 1


def test_completed_occurrence_preserved_when_regenerating(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Monday",
        days_of_week=[0],
        clock_today=today,
    )
    policies = PolicySnapshot(routine_horizon_days=14)
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=policies,
    )
    occurrence, _ = routine_service.list_pending_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )[0]
    routine_service.complete_occurrence(
        db_session,
        occurrence_id=occurrence.id,
        owner_id=LOCAL_OWNER_ID,
    )
    routine_service.ensure_occurrences(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        clock_today=today,
        policies=policies,
    )
    completed = db_session.scalar(
        select(Occurrence).where(Occurrence.id == occurrence.id)
    )
    assert completed is not None
    assert completed.status == OccurrenceStatus.COMPLETED.value
