"""Weekly target ORM model."""

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from planforge.domain.enums import WeeklyTargetStatus


class WeeklyTarget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Goal to complete an activity N times per week."""

    __tablename__ = "weekly_targets"
    __table_args__ = (Index("ix_weekly_targets_owner_status", "owner_id", "status"),)

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    target_count: Mapped[int] = mapped_column(nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WeeklyTargetStatus.ACTIVE.value,
    )

    @property
    def target_status(self) -> WeeklyTargetStatus:
        return WeeklyTargetStatus(self.status)
