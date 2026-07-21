# Date and time design (draft for ADR 0006)

This document supports discussion of [ADR 0006](../decisions/0006-date-time-design-pending.md).
It is **not** a final decision. After review, accepted choices move into ADR 0006
with status **Accepted**.

## Why this matters

Planner bugs often come from mixing:

- **Date-only** values ("due on Friday") with
- **Instants** ("appointment at 10:00 America/Los_Angeles") and
- **Recurrence** (DST gaps and overlaps)

Getting this wrong breaks routines, maintenance intervals, and Week boundaries.

## Questions ADR 0006 must answer

1. Which fields are date-only vs UTC instant vs local date-time?
2. What timezone is authoritative for display and day boundaries?
3. How does the system behave when the OS timezone changes?
4. What week-start day is used (ties to `week.start_day` policy)?
5. How are DST transitions handled for recurring rules?

## Proposed entity field types

| Entity / field | Proposed type | Notes |
|----------------|---------------|-------|
| Task `due_date` | **Local date** (no time) | "Due Friday" regardless of clock |
| Appointment `starts_at`, `ends_at` | **UTC instant** + display TZ | Store UTC; render in user TZ |
| Occurrence `scheduled_date` | **Local date** | One occurrence per calendar day for MVP |
| Occurrence `scheduled_time` (optional) | **Local time** or null | For timed routines later |
| Maintenance `last_completed_at` | **UTC instant** | Exact completion moment |
| Maintenance `next_due_date` | **Local date** | User-facing due day |
| Completion record `recorded_at` | **UTC instant** | Audit trail |
| Week boundaries | **Local date** range | Derived from `week.start_day` |

**DECISION NEEDED:** Confirm table above.

## Timezone strategy (options)

### Option A — Local timezone from OS (recommended for MVP)

- Installation uses system timezone for day boundaries and display.
- Persist a `timezone` preference string (IANA, e.g. `America/Los_Angeles`).
- Default: detect from OS on first run; user can override in settings.

**Pros:** Simple mental model for single-user desktop use.
**Cons:** Phone access later must sync same preference.

### Option B — Fixed UTC everywhere

- All display converted from UTC by client.

**Pros:** Easy storage.
**Cons:** "Today" is wrong for evening users; poor fit for personal planner.

### Option C — Per-event timezone (appointments only)

- Tasks use local; appointments store their own TZ.

**Pros:** Travel-friendly appointments.
**Cons:** More complexity; likely post-MVP.

**Recommendation:** Option A for MVP; Option C as additive later.

## Day boundary

Align with policy `day_boundary.time`:

- MVP: **local midnight** defines "today."
- Post-MVP: optional custom rollover hour (e.g. 4 AM) for night owls.

**DECISION NEEDED:** Include custom hour in MVP or defer?

## Week start

Align with policy `week.start_day` (default `monday`).

Week range = start-of-week 00:00 local through end-of-week 23:59:59 local.

## DST and recurrence

User-written occurrence generation must handle:

- **Spring forward:** missing local times → skip or shift occurrence (policy)
- **Fall back:** duplicated local times → single occurrence (policy)

Document chosen behavior in ADR 0006 when routine slice starts.

**DECISION NEEDED:** Default DST policy for missed generation slot?

## Timezone change mid-use

When user changes OS or app timezone preference:

| Data | Proposed behavior |
|------|-------------------|
| Date-only fields | Unchanged (same calendar date) |
| UTC instants | Unchanged instant; display updates |
| "Today" view | Recomputed on next load |
| Future occurrences | Regenerate from definitions |

**DECISION NEEDED:** Regenerate occurrences immediately or on next horizon roll?

## Value objects (for Phase 6 specs)

Suggested types for you to implement (specs only until approved):

- `LocalDate` — calendar date without timezone
- `UtcInstant` — immutable point in time
- `Week` — start date + `week.start_day` rule
- `Day` — single local date with boundary helpers

Infrastructure timestamps (`created_at` / `updated_at`) remain UTC instants and
are not planner semantics.

## Next step

Review this draft, answer `DECISION NEEDED` items, then we update ADR 0006 to
**Accepted** with final decisions before Slice 3+ (appointments/routines).
