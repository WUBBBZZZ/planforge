# ADR 0006: Date and time design (pending)

## Status

Proposed — requires dedicated requirements phase

## Context

Planner behavior depends on date-only vs timestamp values, timezones, DST,
week-start preferences, and behavior when the device timezone changes.
Implementing schema or recurrence logic before these rules are defined risks
costly rework.

## Decision (interim)

- **No planner date/time schema is implemented** until ADR 0006 is accepted.
- Phase 3 (product requirements) must define:
  - Which entities use date-only vs UTC timestamps
  - Timezone storage and display strategy
  - DST-safe recurrence rules
  - Week-start preference and timezone-change behavior

## Consequences

- Backend migrations for planner tables wait on this ADR.
- Generic timestamp mixins in infrastructure code are UTC-oriented placeholders
  only, not planner semantics.
