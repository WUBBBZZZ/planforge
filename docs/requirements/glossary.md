# Glossary

Canonical terms for Planforge. Use these names in code, API schemas, UI copy,
and tests unless an ADR explicitly renames them.

## Core entities

### Task

A one-time action the user intends to complete. May have a due date, category,
tags, and priority. Distinct from backlog items that are not yet scheduled.

**Example (fabricated):** "Buy example groceries for demo kitchen."

### Backlog item

Something the user wants to do eventually but has not assigned to a specific day
or week. Backlog items can be **promoted** into tasks or routine definitions.

**Example:** "Research fictional calendar apps."

### Appointment

A time-bound obligation with a start (and usually end) time. Entered manually in
early versions. Not generated from recurrence rules.

**Example:** "Demo dentist checkup — Tuesday 10:00."

### Routine

A user-defined recurring pattern (e.g. daily, weekly on Monday/Wednesday) that
**generates occurrences** over a planning horizon. The routine is the definition;
occurrences are the concrete instances on specific dates.

**Example:** "Morning stretch routine — weekdays."

### Occurrence

A single instance of a routine on a calendar date (or date-time window). Users
complete, skip, or miss occurrences; policies govern what happens next.

### Maintenance definition

A long-horizon recurring obligation with a **reschedule interval** (e.g. "change
air filter every 90 days"). Distinct from routines in UX and policy defaults but
may share recurrence machinery internally.

**Example:** "Replace demo water filter — every 3 months."

### Target (weekly target)

A numeric or checklist goal for a week (e.g. "Exercise 3 times"). Progress is
derived from completion history, not from a single due date.

## Planning views

### Today

Items visible for the current calendar day in the user's locale: tasks due today,
today's occurrences, today's appointments, and optionally rolled-over items per
policy.

### Week

A rolling or calendar week (see ADR 0006 for week-start) showing tasks, targets,
occurrences, and appointments in that range.

### Month

Calendar month overview for appointments and high-level density; not every entity
type need appear at month granularity in MVP.

## History and metadata

### Completion record

An immutable (append-only) log entry that an item or occurrence was completed,
skipped, or marked missed, with a timestamp. Used for analytics and audit; not
edited in place.

### Category / tag

User-defined labels for filtering and grouping. Categories are typically single-
select; tags are multi-select. Both are optional on entities.

## Configuration (not entities)

### Policy

A named, UI-configurable rule (e.g. rollover behavior, missed-routine handling).
Policies are settings, not rows in the planner database — though their values are
persisted per installation/user.

### Preference

User choices that affect display only (theme, week start, default Today filters).
Distinct from policies that change planner semantics.

## Explicit non-goals in MVP glossary

- **User account** — deferred; single logical user per installation for now.
- **Sync conflict** — offline/sync vocabulary deferred to service-worker phase.
- **Import / restore** — file-based restore is a later security-reviewed feature.
