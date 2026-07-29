"""Routine occurrence ORM model."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import OccurrenceStatus

if TYPE_CHECKING:
    from planforge.models.routine import Routine


class Occurrence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Single scheduled instance of a routine."""

    __tablename__ = "occurrences"
    __table_args__ = (
        Index("ix_occurrences_owner_date", "owner_id", "scheduled_date"),
        Index("ix_occurrences_routine_date", "routine_id", "scheduled_date"),
        UniqueConstraint(
            "routine_id",
            "scheduled_date",
            name="uq_occurrences_routine_scheduled_date",
        ),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    routine_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("routines.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OccurrenceStatus.PENDING.value,
    )

    routine: Mapped[Routine] = relationship(back_populates="occurrences")

    @property
    def occurrence_status(self) -> OccurrenceStatus:
        return OccurrenceStatus(self.status)
