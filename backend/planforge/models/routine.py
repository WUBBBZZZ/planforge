"""Routine ORM model."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import RoutineStatus

if TYPE_CHECKING:
    from planforge.models.occurrence import Occurrence


class Routine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Recurring activity definition."""

    __tablename__ = "routines"
    __table_args__ = (Index("ix_routines_owner_status", "owner_id", "status"),)

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    schedule_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="weekly",
    )
    days_of_week: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="[0,1,2,3,4]",
    )
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interval_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    starts_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RoutineStatus.ACTIVE.value,
    )

    occurrences: Mapped[list[Occurrence]] = relationship(back_populates="routine")

    @property
    def routine_status(self) -> RoutineStatus:
        return RoutineStatus(self.status)
