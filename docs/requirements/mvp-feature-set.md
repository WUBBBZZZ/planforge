# Minimum viable feature set (MVP)

The smallest set of **vertical slices** that prove the planning engine end-to-end.
Each slice ships domain logic (user-implemented) + persistence + API + UI.

ADR 0006 is **accepted** — date/time rules are locked for implementation.

## Slice 0 — Foundation (done)

- Health check, config, DB scaffolding, UI shell, generic primitives
- Requirements documents and ADR 0006

## Slice 1 — One-time tasks + Today view

**Includes:**

- Task CRUD (fabricated demo data)
- Today view assembly (hard-coded policy defaults first, then settings UI)
- Complete / cancel task
- Completion record append
- Task `due_date` as **local date** per ADR 0006

**Excludes:** rollover policies, backlog, routines

**Exit:** AC-TOD-1, AC-TOD-2, AC-CAP-2, AC-NF-*

## Slice 2 — Backlog + promotion

**Includes:**

- Backlog list and capture-to-backlog
- Promote to dated task
- Backlog lifecycle states

**Exit:** AC-CAP-1, AC-PLW-1

## Slice 3 — Routine definition + occurrences

**Includes:**

- Routine CRUD, pause/archive
- Occurrence generation (user-written engine; DST defaults in ADR 0006)
- Complete / skip occurrence
- Week view shows occurrences

**Exit:** AC-ROU-1, AC-ROU-2, AC-ROU-3

## Slice 4 — Appointments (manual entry)

**Includes:**

- Create/edit appointment with UTC `starts_at` / `ends_at`
- Show in Today and Week

**Exit:** AC-APT-1, AC-APT-2

## Slice 5 — Policies UI

**Includes:**

- Settings screen for policies in [configurable-policies.md](configurable-policies.md)
- Server-side validation and persistence
- Today/Week respect policies

**Exit:** AC-SET-1, AC-SET-2

## Slice 6 — Weekly targets

**Includes:**

- Define weekly target
- Progress from completion records
- Week view summary

**Exit:** AC-PLW-3

## Slice 7 — Maintenance definitions

**Includes:**

- Maintenance CRUD and due scheduling
- Today surfacing within lead days

**Exit:** AC-MNT-1, AC-MNT-2

## Post-MVP (explicitly not in MVP)

- Authentication
- Service worker / offline
- Month view density
- Analytics dashboards
- Export / import UI
- Tailscale / phone access
- PostgreSQL option
- Custom day-boundary hour

## Slice order (accepted)

Tasks → Backlog → **Routines** → **Appointments** → Policies → Weekly targets → Maintenance
