"""Tests for SQLite backup verification."""

import sqlite3
from pathlib import Path

import pytest
from planforge.db.backup_verification import (
    create_backup,
    integrity_check,
    verify_in_isolated_instance,
)


def test_backup_integrity_and_isolated_verification(tmp_path: Path) -> None:
    source = tmp_path / "live.db"
    backup = tmp_path / "backup.db"

    connection = sqlite3.connect(source)
    try:
        connection.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, title TEXT)")
        connection.execute("INSERT INTO demo (title) VALUES ('fabricated')")
        connection.commit()
    finally:
        connection.close()

    create_backup(source, backup)
    assert integrity_check(backup) == "ok"
    verify_in_isolated_instance(backup)


def test_backup_refuses_existing_target(tmp_path: Path) -> None:
    source = tmp_path / "live.db"
    backup = tmp_path / "backup.db"
    backup.write_text("existing")

    connection = sqlite3.connect(source)
    connection.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY)")
    connection.commit()
    connection.close()

    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        create_backup(source, backup)
