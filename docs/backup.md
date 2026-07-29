# SQLite backup

Planforge stores planner data in a local SQLite file (default:
`data/planforge.db`). Backups must never overwrite the live database while
being verified.

## Safe manual process

1. **Stop application writes**
   - Stop uvicorn / the backend API.
   - Close any SQLite browser or editor connected to the live file.

2. **Create a consistent backup**
   - Use SQLite's online backup API (not a plain file copy while writers are
     active).
   - The helper script below calls `sqlite3.Connection.backup()`.

3. **Run `PRAGMA integrity_check` on the copy**
   - The verification script runs this against the backup file only.

4. **Test the copy in an isolated temporary instance**
   - The verification script copies the backup into a temp directory and runs a
     minimal read query. The live database is never opened for write during
     verification.

5. **Store the verified backup**
   - Keep timestamped files under `data/backups/`.
   - Restore only by copying a verified backup to a **new** path and pointing
     `PLANFORGE_DATABASE_URL` at that path.

## PowerShell helper

From the repository root:

```powershell
.\scripts\backup-sqlite.ps1
```

Options:

- `-DatabasePath` — override the live database path
- `-BackupDirectory` — override the output directory (default: `data/backups`)
- `-SkipStopPrompt` — only for automation; not recommended for manual use

The script prompts before proceeding and refuses to overwrite an existing backup
file.

## What is intentionally not included

- **Arbitrary file import** is not implemented. Importing untrusted SQLite files
  requires a separate security review.
- **Phone or remote access** is not enabled. Backups are local-only.
- **Automatic scheduled backups** are planned; manual verification remains the
  supported workflow for now.

## Restore (manual)

1. Stop the backend.
2. Copy a verified backup to a new file, e.g. `data/planforge-restored.db`.
3. Set `PLANFORGE_DATABASE_URL=sqlite:///./data/planforge-restored.db` in `.env`.
4. Start the backend and confirm `/api/health` responds.
5. Spot-check Today/Week views with fabricated demo data only.

## Related decisions

- [ADR 0002: SQLite default database](decisions/0002-sqlite-default-database.md)
- [ADR 0008: SQLite backup process](decisions/0008-sqlite-backup-process.md)
