# Date and time design

Supports [ADR 0006](../decisions/0006-date-time-design.md). **Accepted** as of
2026-07-21 with the decisions below.

## Why this matters

Planner bugs often come from mixing date-only values, UTC instants, recurrence,
and DST. This document locks field types and timezone rules before schema work.

## Accepted decisions

| # | Topic | Decision |
|---|-------|----------|
| 1 | Entity field types | **Accepted** — see table below |
| 2 | Timezone strategy | **Option A** — IANA timezone preference; default from OS |
| 3 | Custom day-boundary hour | **Deferred** — MVP uses local midnight only |
| 4 | Week start | **Monday** default (`week.start_day` = `monday`) |
| 5 | DST recurrence | **Recommended defaults** — see below; refine during routine slice if needed |
| 6 | Timezone change | **Regenerate on next horizon roll** — see below |
| 7 | MVP slice order | **Routines before appointments** |

## Entity field types (accepted)

| Entity / field | Type | Notes |
|----------------|------|-------|
| Task `due_date` | **Local date** | "Due Friday" regardless of clock |
| Appointment `starts_at`, `ends_at` | **UTC instant** + display TZ | Store UTC; render in user TZ |
| Occurrence `scheduled_date` | **Local date** | One occurrence per calendar day for MVP |
| Occurrence `scheduled_time` (optional) | **Local time** or null | Timed routines post-MVP |
| Maintenance `last_completed_at` | **UTC instant** | Exact completion moment |
| Maintenance `next_due_date` | **Local date** | User-facing due day |
| Completion record `recorded_at` | **UTC instant** | Audit trail |
| Week boundaries | **Local date** range | Derived from `week.start_day` |

## Timezone strategy (Option A)

- Persist `timezone` as an IANA string (e.g. `America/Los_Angeles`).
- Default: detect from OS on first run; user may override in settings later.
- Day boundaries and "Today" use this timezone.
- `created_at` / `updated_at` remain UTC; they are not planner semantics.

## Day boundary

- MVP: **local midnight** in the configured timezone defines "today."
- Custom rollover hour (e.g. 4 AM): **deferred** post-MVP.

## Week start

- Default **Monday**; configurable via `week.start_day` policy.
- Week range: Monday 00:00:00 local through Sunday 23:59:59 local (when default).

## DST and recurrence (recommended defaults)

When clocks **spring forward**, some local times do not exist (e.g. 2:30 AM).
When clocks **fall back**, some local times occur twice.

**Recommended behavior for occurrence generation (you implement in routine slice):**

| Situation | Behavior |
|-----------|----------|
| Spring forward — slot missing | **Skip** that occurrence for that calendar day |
| Fall back — slot duplicated | **One** occurrence on that calendar date |
| Date-only routines (no time) | Unaffected by DST |

You may adjust this when writing the generator; document any change in a follow-up ADR note.

## Timezone change mid-use

**What this means:** If you change the Windows timezone or the app timezone
setting, should Planforge immediately rewrite all future routine occurrences in
the database, or wait?

**Accepted approach: regenerate on next horizon roll.**

1. Detect that `timezone` preference changed (store last-used value).
2. **Do not** rewrite the database synchronously on save.
3. On the next occurrence **horizon extension** (app open, routine view load, or
   scheduled roll that generates the next N days), **drop pending future
   occurrences** and regenerate from active routine definitions using the new
   timezone.
4. Date-only fields and completed history stay unchanged.
5. UTC instants (appointments, completion times) keep the same instant; only
   display changes.

## Value objects (Phase 6)

Suggested types for implementation specs:

- `LocalDate` — calendar date without timezone
- `UtcInstant` — immutable point in time
- `Week` — start date + `week.start_day` rule
- `Day` — single local date with boundary helpers

## Unblocks

- Slice 1–2: task `due_date` as local date
- Slice 3: routines and occurrences
- Slice 4: appointments with UTC instants
- Slice 7: maintenance dates
