"""Tests for packing list service."""

from planforge.core.exceptions import ValidationError
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import PackingEntryType, PackingQuestionAnswer
from planforge.services import packing_list_service


def test_create_list_with_items_and_questions(db_session) -> None:
    packing_list = packing_list_service.create_packing_list(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Beach weekend",
        notes="July trip",
    )
    item = packing_list_service.create_entry(
        db_session,
        list_id=packing_list.id,
        owner_id=LOCAL_OWNER_ID,
        entry_type=PackingEntryType.ITEM,
        title="Sunscreen",
    )
    question = packing_list_service.create_entry(
        db_session,
        list_id=packing_list.id,
        owner_id=LOCAL_OWNER_ID,
        entry_type=PackingEntryType.QUESTION,
        title="Do I need swim trunks?",
    )

    detail = packing_list_service.get_packing_list(
        db_session,
        list_id=packing_list.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert detail.title == "Beach weekend"
    assert len(detail.entries) == 2
    assert item.packing_entry_type is PackingEntryType.ITEM
    assert question.packing_entry_type is PackingEntryType.QUESTION


def test_answer_question_and_check_item(db_session) -> None:
    packing_list = packing_list_service.create_packing_list(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Conference",
    )
    item = packing_list_service.create_entry(
        db_session,
        list_id=packing_list.id,
        owner_id=LOCAL_OWNER_ID,
        entry_type=PackingEntryType.ITEM,
        title="Laptop charger",
    )
    question = packing_list_service.create_entry(
        db_session,
        list_id=packing_list.id,
        owner_id=LOCAL_OWNER_ID,
        entry_type=PackingEntryType.QUESTION,
        title="Do I need formal clothes?",
    )

    packing_list_service.update_entry(
        db_session,
        entry_id=item.id,
        owner_id=LOCAL_OWNER_ID,
        is_checked=True,
    )
    answered = packing_list_service.update_entry(
        db_session,
        entry_id=question.id,
        owner_id=LOCAL_OWNER_ID,
        answer=PackingQuestionAnswer.YES,
    )
    assert answered.answer == "yes"

    try:
        packing_list_service.update_entry(
            db_session,
            entry_id=question.id,
            owner_id=LOCAL_OWNER_ID,
            is_checked=True,
        )
        raise AssertionError("expected ValidationError")
    except ValidationError:
        pass


def test_delete_list_cascades_entries(db_session) -> None:
    packing_list = packing_list_service.create_packing_list(
        db_session,
        owner_id=LOCAL_OWNER_ID,
        title="Short trip",
    )
    packing_list_service.create_entry(
        db_session,
        list_id=packing_list.id,
        owner_id=LOCAL_OWNER_ID,
        entry_type=PackingEntryType.ITEM,
        title="Passport",
    )
    packing_list_service.delete_packing_list(
        db_session,
        list_id=packing_list.id,
        owner_id=LOCAL_OWNER_ID,
    )
    assert packing_list_service.list_packing_lists(db_session, owner_id=LOCAL_OWNER_ID) == []
