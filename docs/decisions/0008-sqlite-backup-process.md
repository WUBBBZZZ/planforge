# ADR 0008: SQLite backup process

## Status

Accepted

## Context

Planforge is local-first with SQLite as the default database. Users need a safe
way to back up planner data without corrupting the live file or importing
untrusted content.

## Decision

1. Manual backups use SQLite's `backup()` API, not raw copies while writers are
   active.
2. Every backup is verified with `PRAGMA integrity_check` on the **copy** only.
3. Verification opens the copy in a temporary isolated file; the live database
   is never overwritten during verification.
4. A PowerShell helper (`scripts/backup-sqlite.ps1`) guides the operator with
   explicit prompts and no destructive defaults.
5. Arbitrary file import remains out of scope until security-reviewed.

## Consequences

- Operators must stop the backend before backup (enforced by prompt).
- Backup and restore workflows are documented in [backup.md](../backup.md).
- Automated cloud backup is deferred.
