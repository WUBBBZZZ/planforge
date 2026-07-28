"""Backlog item ORM model."""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import BacklogStatus


class BacklogItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Captured idea awaiting promotion to a dated entity."""

    __tablename__ = "backlog_items"
    __table_args__ = (Index("ix_backlog_owner_status", "owner_id", "status"),)

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BacklogStatus.ACTIVE.value,
    )
    promoted_entity_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    promoted_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_entity_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    @property
    def backlog_status(self) -> BacklogStatus:
        return BacklogStatus(self.status)
