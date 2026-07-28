"""Routine occurrence ORM model."""

from datetime import date

from sqlalchemy import Date, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import OccurrenceStatus


class Occurrence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Single scheduled instance of a routine."""

    __tablename__ = "occurrences"
    __table_args__ = (
        Index("ix_occurrences_owner_date", "owner_id", "scheduled_date"),
        Index("ix_occurrences_routine_date", "routine_id", "scheduled_date"),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    routine_id: Mapped[str] = mapped_column(String(36), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OccurrenceStatus.PENDING.value,
    )

    @property
    def occurrence_status(self) -> OccurrenceStatus:
        return OccurrenceStatus(self.status)
