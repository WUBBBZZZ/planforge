"""Tests for database session helpers."""

from pathlib import Path

from planforge.db.session import _ensure_sqlite_parent_dir, create_engine


def test_create_engine_creates_sqlite_parent_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "planforge.db"
    database_url = f"sqlite:///{db_path.as_posix()}"

    engine = create_engine(database_url)
    try:
        assert db_path.parent.is_dir()
        assert engine.url.database is not None
    finally:
        engine.dispose()


def test_ensure_sqlite_parent_dir_ignores_memory() -> None:
    _ensure_sqlite_parent_dir("sqlite:///:memory:")
