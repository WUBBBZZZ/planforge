"""Database migration helpers."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_database() -> None:
    """Apply pending Alembic migrations."""
    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    command.upgrade(config, "head")
