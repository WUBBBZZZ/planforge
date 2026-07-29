"""Database migration tests."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from planforge.core.config import get_settings
from planforge.db.migrations import upgrade_database
from sqlalchemy import create_engine, inspect


def _alembic_config(database_url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_fresh_database_migrations(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "fresh.db"
    database_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("PLANFORGE_DATABASE_URL", database_url)
    get_settings.cache_clear()

    upgrade_database()

    engine = create_engine(database_url)
    try:
        table_names = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert "tasks" in table_names
    assert "appointments" in table_names
    assert "maintenance_definitions" in table_names
    assert "maintenance_completions" in table_names
    assert "alembic_version" in table_names


def test_upgrade_from_previous_schema(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "previous.db"
    database_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("PLANFORGE_DATABASE_URL", database_url)
    get_settings.cache_clear()

    config = _alembic_config(database_url)
    command.upgrade(config, "0007_appointment_scheduling")

    engine = create_engine(database_url)
    try:
        tables_before = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert "appointments" in tables_before
    assert "maintenance_completions" not in tables_before

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        tables_after = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert "maintenance_completions" in tables_after
