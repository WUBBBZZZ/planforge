"""Maintenance completion ORM model."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.db.types import UTCDateTime


class MaintenanceCompletion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Recorded maintenance occurrence."""

    __tablename__ = "maintenance_completions"
    __table_args__ = (
        Index(
            "ix_maintenance_completions_definition_date",
            "maintenance_definition_id",
            "completed_on",
        ),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    maintenance_definition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("maintenance_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    completed_on: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_voided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voided_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    superseded_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("maintenance_completions.id", ondelete="SET NULL"),
        nullable=True,
    )
