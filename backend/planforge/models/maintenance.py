"""Maintenance definition ORM model."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import (
    MaintenanceIntervalUnit,
    MaintenanceNextActionStatus,
    MaintenanceStatus,
)


class MaintenanceDefinition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Long-term recurring maintenance item."""

    __tablename__ = "maintenance_definitions"
    __table_args__ = (
        Index("ix_maintenance_owner_status", "owner_id", "status"),
        Index("ix_maintenance_owner_due", "owner_id", "next_due_date"),
        Index(
            "ix_maintenance_owner_next_action",
            "owner_id",
            "next_action_status",
        ),
        UniqueConstraint(
            "linked_appointment_id",
            name="uq_maintenance_linked_appointment",
        ),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    interval_unit: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=MaintenanceIntervalUnit.MONTHS.value,
    )
    interval_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_action_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MaintenanceNextActionStatus.NO_NEXT_DATE.value,
    )
    linked_appointment_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
    )
    scheduling_reminder_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reminder_offset_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MaintenanceStatus.ACTIVE.value,
    )

    @property
    def maintenance_status(self) -> MaintenanceStatus:
        return MaintenanceStatus(self.status)

    @property
    def interval(self) -> MaintenanceIntervalUnit:
        return MaintenanceIntervalUnit(self.interval_unit)

    @property
    def next_action(self) -> MaintenanceNextActionStatus:
        return MaintenanceNextActionStatus(self.next_action_status)
