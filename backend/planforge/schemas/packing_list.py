"""Pydantic schemas for packing lists."""

from planforge.domain.enums import PackingEntryType, PackingQuestionAnswer
from planforge.models.packing_list import PackingList, PackingListEntry
from pydantic import BaseModel, Field


class PackingListEntryResponse(BaseModel):
    id: str
    list_id: str
    entry_type: PackingEntryType
    title: str
    sort_order: int
    is_checked: bool
    answer: PackingQuestionAnswer | None

    @classmethod
    def from_entry(cls, entry: PackingListEntry) -> PackingListEntryResponse:
        return cls(
            id=entry.id,
            list_id=entry.list_id,
            entry_type=entry.packing_entry_type,
            title=entry.title,
            sort_order=entry.sort_order,
            is_checked=entry.is_checked,
            answer=entry.question_answer,
        )


class PackingListSummaryResponse(BaseModel):
    id: str
    title: str
    notes: str | None
    sort_order: int
    item_count: int
    question_count: int

    @classmethod
    def from_list(cls, packing_list: PackingList) -> PackingListSummaryResponse:
        items = [
            entry
            for entry in packing_list.entries
            if entry.packing_entry_type is PackingEntryType.ITEM
        ]
        questions = [
            entry
            for entry in packing_list.entries
            if entry.packing_entry_type is PackingEntryType.QUESTION
        ]
        return cls(
            id=packing_list.id,
            title=packing_list.title,
            notes=packing_list.notes,
            sort_order=packing_list.sort_order,
            item_count=len(items),
            question_count=len(questions),
        )


class PackingListDetailResponse(BaseModel):
    id: str
    title: str
    notes: str | None
    sort_order: int
    entries: list[PackingListEntryResponse]

    @classmethod
    def from_list(cls, packing_list: PackingList) -> PackingListDetailResponse:
        return cls(
            id=packing_list.id,
            title=packing_list.title,
            notes=packing_list.notes,
            sort_order=packing_list.sort_order,
            entries=[
                PackingListEntryResponse.from_entry(entry)
                for entry in packing_list.entries
            ],
        )


class PackingListCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str | None = None


class PackingListUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None


class PackingEntryCreateRequest(BaseModel):
    entry_type: PackingEntryType
    title: str = Field(min_length=1, max_length=500)


class PackingEntryUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    is_checked: bool | None = None
    answer: PackingQuestionAnswer | None = None
    clear_answer: bool = False
