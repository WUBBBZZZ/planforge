"""Appointment ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import AppointmentStatus


class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Time-bound commitment stored as UTC instants."""

    __tablename__ = "appointments"
    __table_args__ = (Index("ix_appointments_owner_starts", "owner_id", "starts_at"),)

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AppointmentStatus.SCHEDULED.value,
    )

    @property
    def appointment_status(self) -> AppointmentStatus:
        return AppointmentStatus(self.status)
