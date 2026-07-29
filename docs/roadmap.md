# Roadmap

## Implemented (current portfolio)

- Local-first FastAPI + React + SQLite stack
- Tasks, backlog, routines, appointments, maintenance, weekly targets
- Today / Week / Month planner views with timezone authority
- Dedicated Schedule and Maintenance pages
- Verified SQLite backup workflow
- Test suite with coverage gates and CI

## In progress

- Portfolio documentation and screenshot capture workflow
- Continued hardening of maintenance and appointment edge cases

## Planned (requires explicit approval)

### Security and access

- Authentication (ADR 0004)
- Tailscale Serve for private phone access — **no Funnel, no port forwarding**
- Service worker / offline caching security gate (ADR 0005)
- Arbitrary database import (security-reviewed)

### Product

- Capture improvements and unified command palette
- Notification reminders (local only)
- PostgreSQL deployment option
- Automated backup scheduling with retention policy
- Deployment packaging (Windows service / container)

### Quality

- Visual regression tests for planner layouts
- Expanded accessibility audits (keyboard-only flows)
- Performance profiling for large maintenance histories

## Non-goals (current phase)

- Public internet exposure
- LAN-wide access without authentication
- Cloud sync or multi-tenant hosting
- Real personal data in repository fixtures

See [feature-status.md](feature-status.md) for a detailed matrix.
