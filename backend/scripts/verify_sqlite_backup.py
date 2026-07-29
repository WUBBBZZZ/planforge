"""Create and verify a SQLite backup without touching the live database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from planforge.db.backup_verification import (
    create_backup,
    integrity_check,
    verify_in_isolated_instance,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--backup", required=True, type=Path)
    args = parser.parse_args(argv)

    source_path = args.source.resolve()
    backup_path = args.backup.resolve()

    if not source_path.exists():
        print(f"Source database not found: {source_path}", file=sys.stderr)
        return 1

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if backup_path.exists():
        print(f"Refusing to overwrite existing backup: {backup_path}", file=sys.stderr)
        return 1

    print(f"Creating backup from {source_path}")
    create_backup(source_path, backup_path)

    print("Running PRAGMA integrity_check on backup copy")
    result = integrity_check(backup_path)
    if result != "ok":
        backup_path.unlink(missing_ok=True)
        print(f"integrity_check failed: {result}", file=sys.stderr)
        return 1

    print("Testing backup in isolated temporary instance")
    try:
        verify_in_isolated_instance(backup_path)
    except RuntimeError as error:
        backup_path.unlink(missing_ok=True)
        print(str(error), file=sys.stderr)
        return 1

    print("integrity_check: ok")
    print("isolated verification: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
