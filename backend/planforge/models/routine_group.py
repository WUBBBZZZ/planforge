"""Routine group ORM model."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from planforge.models.routine import Routine


class RoutineGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-defined grouping for routines with planner visibility."""

    __tablename__ = "routine_groups"
    __table_args__ = (
        Index("ix_routine_groups_owner_sort", "owner_id", "sort_order"),
        UniqueConstraint("owner_id", "name", name="uq_routine_groups_owner_name"),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    week_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    month_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    routines: Mapped[list[Routine]] = relationship(back_populates="group")
