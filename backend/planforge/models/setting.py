"""User setting ORM model."""

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from planforge.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Setting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Key-value preference or policy for an owner."""

    __tablename__ = "settings"
    __table_args__ = (
        UniqueConstraint("owner_id", "key", name="uq_settings_owner_key"),
        Index("ix_settings_owner", "owner_id"),
    )

    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(String(256), nullable=False)
