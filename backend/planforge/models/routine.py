"""Routine ORM model."""

from datetime import date

from sqlalchemy import Date, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import RoutineStatus


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

    @property
    def routine_status(self) -> RoutineStatus:
        return RoutineStatus(self.status)
