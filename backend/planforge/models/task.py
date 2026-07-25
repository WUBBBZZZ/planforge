"""Task ORM model."""

from datetime import date

from sqlalchemy import Date, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import TaskStatus


class Task(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One-time task with optional local due date."""

    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_owner_status_due_date", "owner_id", "status", "due_date"),
        Index("ix_tasks_owner_due_date", "owner_id", "due_date"),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TaskStatus.PENDING.value,
    )

    @property
    def task_status(self) -> TaskStatus:
        return TaskStatus(self.status)
