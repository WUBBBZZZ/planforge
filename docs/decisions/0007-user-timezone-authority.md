# ADR 0007: User timezone authority and read-path integrity

## Status

**Accepted** (2026-07-28)

## Context

Planforge previously mixed three timezone sources:

- `PLANFORGE_TIMEZONE` environment variable (server "today" and occurrence generation)
- Database `timezone` setting (appointment and completion bucketing)
- Browser-local defaults (routine `starts_on`, appointment capture, time display)

Weekly targets additionally counted progress using raw UTC midnights while
completion overlays used policy-timezone midnights. SQLite returns naive
datetimes for `DateTime(timezone=True)` columns, so `.astimezone()` could
reinterpret stored UTC values using the host OS zone.

GET view endpoints also performed hidden writes: seeding missing settings and
generating routine occurrences, then committing via the shared `get_db` dependency.

## Decision

### Timezone authority

1. The database `timezone` setting is the **authoritative planner timezone** for
   all backend calendar bucketing, "today" resolution, and occurrence generation.
2. `PLANFORGE_TIMEZONE` seeds the `timezone` setting **only on first run** when
   no row exists. It is not consulted at runtime afterward.
3. The backend performs authoritative date bucketing. Stored instants remain UTC;
   date-only planner values remain date-only ISO strings.
4. The frontend sends explicit ISO values and displays times using the configured
   planner timezone from settings (not silent browser substitution for planning).

### SQLite datetimes

Use a `UTCDateTime` SQLAlchemy type and `as_utc_aware()` normalization so values
read from SQLite are always UTC-aware before `.astimezone()`.

### Occurrence uniqueness

Add a unique constraint on `(routine_id, scheduled_date)`. Before migration,
deduplicate existing rows: prefer completed/skipped over pending; among pending
duplicates keep the oldest `created_at`. Never delete completion history.

### Read-path writes

GET `/api/views/*` endpoints are read-only. Settings seeding runs at application
startup. Occurrence generation runs at startup, after routine mutations, and via
`POST /api/routines/sync-occurrences`.

### Referential integrity

- Add `occurrences.routine_id → routines.id` with `ON DELETE CASCADE` (routines are
  archived, not hard-deleted, in normal operation).
- Polymorphic `completion_records` remain without foreign keys (entity_type +
  entity_id cannot be enforced safely).
- Weekly target deletion explicitly deletes related `completion_records` for that
  target (deliberate cascade, not orphaning).

## Migration and compatibility risks

| Risk | Mitigation |
|------|------------|
| Duplicate occurrences block unique index | Pre-migration dedupe preserves completed/skipped rows |
| Existing DB missing timezone row | Startup `ensure_default_settings` still inserts defaults |
| Views empty until sync | Startup sync + frontend POST sync on planner page load |
| Env timezone ignored after upgrade | Documented; user sets timezone via Settings API/UI |
| FK addition on SQLite | Alembic `batch_alter_table` |
| Changing timezone mid-week | Tests cover boundary shifts; progress recounts on next read |

## Consequences

- Single timezone source simplifies DST and midnight-boundary behavior.
- GET views no longer have side effects.
- Occurrence generation races are blocked at the database layer.
- Polymorphic completions remain application-validated.
