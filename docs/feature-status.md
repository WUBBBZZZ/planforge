# Feature status

Status legend: **Implemented** · **In progress** · **Planned**

## Core planner

| Feature | Status | Notes |
|---------|--------|-------|
| Tasks (CRUD, complete, cancel, reopen) | **Implemented** | API + Today/Week/Month |
| Move task to backlog | **Implemented** | Provenance preserved |
| Backlog capture and promote | **Implemented** | Promote requires due date |
| Today / Week / Month views | **Implemented** | Planner timezone from settings |
| Weekly targets | **Implemented** | Progress via completion records |
| Settings (timezone, policies) | **Implemented** | UI in Settings page |

## Routines and recurrence

| Feature | Status | Notes |
|---------|--------|-------|
| Weekly routines (interval weeks) | **Implemented** | Anchor-based biweekly support |
| Monthly routines (calendar day) | **Implemented** | End-of-month clamping |
| Occurrence sync horizon | **Implemented** | Configurable via settings |
| Occurrence complete / skip | **Implemented** | |
| DST / timezone integrity | **Implemented** | ADR 0006, 0007 |

## Appointments

| Feature | Status | Notes |
|---------|--------|-------|
| Timed and all-day appointments | **Implemented** | |
| Multi-day spans | **Implemented** | Span metadata in views |
| Lifecycle (complete, cancel, reopen, archive) | **Implemented** | |
| Dedicated Schedule page | **Implemented** | `/schedule` |
| Delete with audit history guard | **Implemented** | |

## Maintenance

| Feature | Status | Notes |
|---------|--------|-------|
| Maintenance definitions | **Implemented** | Calendar-aware intervals |
| Completion history | **Implemented** | Separate completion table |
| Scheduling reminders vs appointments | **Implemented** | Distinct records, linkable |
| Maintenance page + history board | **Implemented** | `/maintenance` |
| Linked appointment workflow | **Implemented** | Cancel → needs scheduling |

## Platform and security

| Feature | Status | Notes |
|---------|--------|-------|
| Loopback-only binding | **Implemented** | 127.0.0.1 default |
| SQLite default database | **Implemented** | Alembic migrations |
| Manual verified backup | **Implemented** | See [backup.md](backup.md) |
| Authentication | **Planned** | ADR 0004 deferred |
| Phone / Tailscale access | **Planned** | Not enabled |
| Service worker / offline cache | **Planned** | ADR 0005 deferred |
| Arbitrary DB import | **Planned** | Requires security review |

## Developer experience

| Feature | Status | Notes |
|---------|--------|-------|
| OpenAPI type generation | **Implemented** | Committed schema + `schema.d.ts` |
| CI (lint, typecheck, test, build) | **Implemented** | GitHub Actions |
| Coverage reporting | **Implemented** | Backend ≥80%, frontend thresholds |
| Dependency lock + audit | **Implemented** | `requirements.lock`, pip-audit, npm audit |

All demo content in tests and documentation uses **fabricated data only**.
