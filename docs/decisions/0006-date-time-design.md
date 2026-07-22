# ADR 0006: Date and time design

## Status

**Accepted** (2026-07-21)

Full detail: [`docs/requirements/date-time-design.md`](../requirements/date-time-design.md)

## Context

Planner behavior depends on date-only vs timestamp values, timezones, DST,
week-start preferences, and behavior when the device timezone changes.

## Decision

### Field types

- Task due dates: **local date**
- Appointments: **UTC instants** with display in user timezone
- Routine occurrences: **local date** (MVP); optional local time later
- Maintenance: `last_completed_at` UTC instant; `next_due_date` local date
- Completion records: `recorded_at` UTC instant
- Week boundaries: local date range from `week.start_day`

### Timezone

- **Option A:** IANA `timezone` preference; default from OS on first run.

### Day boundary

- Local midnight in configured timezone for MVP.
- Custom rollover hour: **deferred**.

### Week start

- Default **Monday** (`week.start_day` = `monday`).

### DST (recommended defaults for routine generator)

- Spring-forward gap: **skip** occurrence that falls in non-existent local time.
- Fall-back duplicate: **one** occurrence per calendar date.
- Date-only routines: unaffected.

Refinable during routine slice implementation without reopening this ADR unless
behavior changes materially.

### Timezone change

- **Regenerate on next horizon roll** — do not synchronously rewrite DB on save.
- Pending future occurrences regenerated when horizon extends after TZ change.
- History and date-only fields unchanged.

### MVP slice order

- Routines (Slice 3) before appointments (Slice 4).

## Consequences

- Planner schema and migrations may proceed for tasks, routines, then
  appointments.
- Routine occurrence generation must implement DST and horizon rules above.
- Infrastructure `created_at`/`updated_at` mixins remain generic UTC metadata.
