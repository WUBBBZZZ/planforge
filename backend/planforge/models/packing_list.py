"""Packing list ORM models."""

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import PackingEntryType, PackingQuestionAnswer


class PackingList(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A reusable packing checklist for a trip or event."""

    __tablename__ = "packing_lists"
    __table_args__ = (Index("ix_packing_lists_owner_sort", "owner_id", "sort_order"),)

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    entries: Mapped[list["PackingListEntry"]] = relationship(
        back_populates="packing_list",
        cascade="all, delete-orphan",
        order_by="PackingListEntry.sort_order",
    )


class PackingListEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An item to pack or a trip-planning question within a list."""

    __tablename__ = "packing_list_entries"
    __table_args__ = (
        Index("ix_packing_list_entries_list_sort", "list_id", "sort_order"),
    )

    list_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("packing_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_checked: Mapped[bool] = mapped_column(nullable=False, default=False)
    answer: Mapped[str | None] = mapped_column(String(8), nullable=True)

    packing_list: Mapped[PackingList] = relationship(back_populates="entries")

    @property
    def packing_entry_type(self) -> PackingEntryType:
        return PackingEntryType(self.entry_type)

    @property
    def question_answer(self) -> PackingQuestionAnswer | None:
        if self.answer is None:
            return None
        return PackingQuestionAnswer(self.answer)
