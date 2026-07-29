"""SQLite backup creation and verification helpers."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path


def create_backup(source_path: Path, backup_path: Path) -> None:
    """Copy source to backup using SQLite's backup API for a consistent snapshot."""
    if backup_path.exists():
        raise RuntimeError(f"Refusing to overwrite existing backup: {backup_path}")

    source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    try:
        backup = sqlite3.connect(str(backup_path))
        try:
            source.backup(backup)
        finally:
            backup.close()
    finally:
        source.close()


def integrity_check(database_path: Path) -> str:
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    try:
        row = connection.execute("PRAGMA integrity_check").fetchone()
        return row[0] if row else "failed"
    finally:
        connection.close()


def verify_in_isolated_instance(backup_path: Path) -> None:
    """Open the backup copy in a temporary file and run a minimal read query."""
    with tempfile.TemporaryDirectory(prefix="planforge-backup-verify-") as temp_dir:
        isolated_copy = Path(temp_dir) / "verify.db"
        isolated_copy.write_bytes(backup_path.read_bytes())

        connection = sqlite3.connect(str(isolated_copy))
        try:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            if not tables:
                raise RuntimeError("Backup copy contains no tables")
            connection.execute("SELECT 1").fetchone()
        finally:
            connection.close()
