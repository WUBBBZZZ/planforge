"""Maintenance definition ORM model."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import MaintenanceStatus


class MaintenanceDefinition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Infrequent recurring maintenance item."""

    __tablename__ = "maintenance_definitions"
    __table_args__ = (
        Index("ix_maintenance_owner_status", "owner_id", "status"),
        Index("ix_maintenance_owner_due", "owner_id", "next_due_date"),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    interval_days: Mapped[int] = mapped_column(nullable=False, default=90)
    last_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MaintenanceStatus.ACTIVE.value,
    )

    @property
    def maintenance_status(self) -> MaintenanceStatus:
        return MaintenanceStatus(self.status)
