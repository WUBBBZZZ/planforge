"""Appointment ORM model."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.db.types import UTCDateTime
from planforge.domain.enums import AppointmentStatus


class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Scheduled obligation with date-only all-day or UTC timed instants."""

    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_owner_starts", "owner_id", "start_date"),
        Index("ix_appointments_owner_status", "owner_id", "status"),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reminder_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maintenance_definition_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("maintenance_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AppointmentStatus.SCHEDULED.value,
    )

    @property
    def appointment_status(self) -> AppointmentStatus:
        return AppointmentStatus(self.status)
