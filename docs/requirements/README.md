# Planforge product requirements

Phase 3 deliverables: domain vocabulary, workflows, lifecycle states, configurable
policies, acceptance criteria, and minimum viable feature set.

These documents describe **what** Planforge should do. They do not implement
planner rules in code. Core behavior (occurrence generation, rollover, missed-item
handling, etc.) is implemented by the project owner against these specs.

## Documents

| Document | Purpose |
|----------|---------|
| [glossary.md](glossary.md) | Shared terminology |
| [workflows.md](workflows.md) | End-user workflows |
| [lifecycle-states.md](lifecycle-states.md) | Entity states and transitions |
| [configurable-policies.md](configurable-policies.md) | Named policy options (UI-configured) |
| [acceptance-criteria.md](acceptance-criteria.md) | Testable criteria per workflow |
| [mvp-feature-set.md](mvp-feature-set.md) | First shippable vertical slices |
| [preferences.md](preferences.md) | Display and UX defaults (landing view, capture) |
| [slices/0001-tasks-today.md](slices/0001-tasks-today.md) | **Slice 1 implementation spec** (tasks, Today, Week) |
| [date-time-design.md](date-time-design.md) | ADR 0006 date/time reference |

## Status

**Accepted** for ADR 0006 and UX/policy defaults (2026-07-22). Minor lifecycle
questions may remain inline as `DECISION NEEDED`.

## Fabricated data

All examples use obviously fake content (e.g. "Alex Example", "Water the plants").
No real personal data in this repository.
