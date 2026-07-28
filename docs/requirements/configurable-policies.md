# Configurable policies

Planner behavior is configured through the UI, not environment variables or
source code. Each policy has a **key**, human-readable **label**, **options**,
and a **default** for new installations.

**Philosophy (accepted 2026-07-22):** Default policies favor **reminders** —
surfacing items for the user to act on — rather than silent auto-changes or
hiding overdue work.

Implementation note: store policy values in a `settings` or `preferences` table;
validate option keys server-side.

Display preferences (landing view, capture modal) live in
[preferences.md](preferences.md).

## Visibility policies

### `today.include_rolled_tasks`

| Option | Behavior |
|--------|----------|
| `yes` | Overdue pending tasks appear in Today (reminder) |
| `no` | Only tasks due today |

**Default:** `yes` — reminder-first: overdue tasks stay visible

### `today.include_routine_occurrences`

| Option | Behavior |
|--------|----------|
| `all_due` | All pending occurrences for today |
| `time_window` | Only occurrences in a configured day window (future) |

**Default:** `all_due`

### `week.show_completed`

| Option | Behavior |
|--------|----------|
| `yes` | Show completed items dimmed |
| `no` | Hide completed items |

**Default:** `no`

### `week.include_overdue_tasks`

| Option | Behavior |
|--------|----------|
| `yes` | Show overdue pending tasks in Week view (reminder) |
| `no` | Only tasks scheduled in that week |

**Default:** `yes` — reminder-first for weekly planning

## Missed-item policies

### `routine.missed_behavior`

| Option | Behavior |
|--------|----------|
| `mark_missed` | Set occurrence to `missed`; no auto-reschedule |
| `roll_forward` | Create or highlight next pending occurrence |
| `prompt` | Remind user on next open; ask how to handle (UI flow) |

**Default:** `prompt` — reminder-first

### `task.overdue_behavior`

| Option | Behavior |
|--------|----------|
| `stay_pending` | Remain pending with original due date; surfaced by visibility policies |
| `roll_to_today` | Due date advances to today when viewed |
| `hide_until_rescheduled` | Drop from active views until user sets new date |

**Default:** `stay_pending` — keep original date; rely on `today.include_rolled_tasks` and `week.include_overdue_tasks` for reminders

## Rollover policies

### `day_boundary.time`

| Option | Behavior |
|--------|----------|
| `midnight_local` | Day rolls at local midnight |
| `custom_hour` | Roll at user-configured hour (e.g. 04:00) |

**Default:** `midnight_local` (custom hour deferred post-MVP)

### `week.start_day`

| Option | Behavior |
|--------|----------|
| `sunday` | Week starts Sunday |
| `monday` | Week starts Monday |
| `saturday` | Week starts Saturday |

**Default:** `monday` (ADR 0006)

## Generation policies

### `routine.horizon_days`

How many days ahead to generate occurrences.

| Option | Value |
|--------|-------|
| `short` | 14 |
| `medium` | 30 |
| `long` | 90 |

**Default:** `medium`

### `maintenance.lead_days`

How many days before due date to show maintenance in Today (reminder window).

**Default:** `7`

## Policy UI requirements

- Each policy appears in Settings with label, short description, and option
  radio/select.
- Changing a policy takes effect on next view assembly (no restart).
- Policies must not require developer mode or JSON editing.

## Out of scope for policy MVP

- Per-category overrides
- A/B testing or rule scripting
- Importing policies from files
- Push/email notifications (in-app reminders only for MVP)
