# Configurable policies

Planner behavior is configured through the UI, not environment variables or
source code. Each policy has a **key**, human-readable **label**, **options**,
and a **default** for new installations.

Implementation note: store policy values in a `settings` or `preferences` table;
validate option keys server-side.

## Visibility policies

### `today.include_rolled_tasks`

| Option | Behavior |
|--------|----------|
| `yes` | Overdue pending tasks appear in Today |
| `no` | Only tasks due today |

**Default:** `yes`

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

## Missed-item policies

### `routine.missed_behavior`

| Option | Behavior |
|--------|----------|
| `mark_missed` | Set occurrence to `missed`; no auto-reschedule |
| `roll_forward` | Create or highlight next pending occurrence |
| `prompt` | Ask user on next open (UI flow) |

**Default:** `mark_missed` — **DECISION NEEDED**

### `task.overdue_behavior`

| Option | Behavior |
|--------|----------|
| `stay_pending` | Remain pending with original due date |
| `roll_to_today` | Due date advances to today when viewed |
| `hide_until_rescheduled` | Drop from Today until user sets new date |

**Default:** `stay_pending`

## Rollover policies

### `day_boundary.time`

| Option | Behavior |
|--------|----------|
| `midnight_local` | Day rolls at local midnight |
| `custom_hour` | Roll at user-configured hour (e.g. 04:00) |

**Default:** `midnight_local` — custom hour is post-MVP unless ADR 0006 adopts it

### `week.start_day`

| Option | Behavior |
|--------|----------|
| `sunday` | Week starts Sunday |
| `monday` | Week starts Monday |
| `saturday` | Week starts Saturday |

**Default:** `monday` — **DECISION NEEDED**

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

How many days before due date to show maintenance in Today.

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
