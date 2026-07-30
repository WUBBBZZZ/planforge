"""Tests for routine group service."""

from planforge.core.exceptions import ValidationError
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.services import routine_group_service, routine_service
from planforge.domain.local_date import LocalDate


def test_ensure_default_groups_creates_misc(db_session) -> None:
    misc = routine_group_service.ensure_default_groups(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )
    assert misc.name == "Misc"
    assert misc.is_system is True
    assert misc.week_visible is False
    assert misc.month_visible is False


def test_create_routine_assigns_misc_group(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Stretch",
        days_of_week=[0],
        clock_today=today,
    )
    assert routine.group_id is not None
    misc = routine_group_service.get_misc_group(db_session, owner_id=LOCAL_OWNER_ID)
    assert routine.group_id == misc.id


def test_visible_routine_ids_respects_week_and_month_visibility(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Stretch",
        days_of_week=[0],
        clock_today=today,
    )
    assert routine_group_service.visible_routine_ids(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        view="week",
    ) == set()
    assert routine_group_service.visible_routine_ids(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        view="month",
    ) == set()

    misc = routine_group_service.get_misc_group(db_session, owner_id=LOCAL_OWNER_ID)
    routine_group_service.update_group(
        db_session,
        group_id=misc.id,
        owner_id=LOCAL_OWNER_ID,
        week_visible=True,
    )
    assert routine_group_service.visible_routine_ids(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        view="week",
    ) == {routine.id}
    assert routine_group_service.visible_routine_ids(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        view="month",
    ) == set()

    routine_group_service.update_group(
        db_session,
        group_id=misc.id,
        owner_id=LOCAL_OWNER_ID,
        month_visible=True,
    )
    assert routine_group_service.visible_routine_ids(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        view="month",
    ) == {routine.id}


def test_delete_group_moves_routines_to_misc(db_session) -> None:
    today = LocalDate.from_iso("2026-07-20")
    custom = routine_group_service.create_group(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        name="Kitchen",
    )
    routine = routine_service.create_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Dishes",
        days_of_week=[0],
        clock_today=today,
    )
    routine_group_service.move_routine(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        routine_id=routine.id,
        group_id=custom.id,
        sort_order=0,
    )
    routine_group_service.delete_group(
        db_session,
        group_id=custom.id,
        owner_id=LOCAL_OWNER_ID,
    )
    misc = routine_group_service.get_misc_group(db_session, owner_id=LOCAL_OWNER_ID)
    db_session.refresh(routine)
    assert routine.group_id == misc.id


def test_cannot_delete_misc_group(db_session) -> None:
    misc = routine_group_service.ensure_default_groups(
        db_session,
        owner_id=LOCAL_OWNER_ID,
    )
    try:
        routine_group_service.delete_group(
            db_session,
            group_id=misc.id,
            owner_id=LOCAL_OWNER_ID,
        )
        raise AssertionError("expected ValidationError")
    except ValidationError:
        pass
