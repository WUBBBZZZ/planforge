"""Completion record ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, UUIDPrimaryKeyMixin


class CompletionRecord(Base, UUIDPrimaryKeyMixin):
    """Append-only completion audit entry."""

    __tablename__ = "completion_records"
    __table_args__ = (
        Index("ix_completion_records_entity", "entity_type", "entity_id"),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
