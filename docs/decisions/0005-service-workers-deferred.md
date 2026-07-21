# ADR 0005: Service workers and offline behavior deliberately deferred

## Status

Accepted

## Context

Service workers, browser storage, and offline mutation queues affect caching,
security boundaries, and conflict resolution.

## Decision

- Frontend skeleton includes **manifest and installability metadata only**.
- No service worker registration, offline caching, or browser persistence for
  planner data or credentials in infrastructure phases.
- A dedicated security gate will cover caching strategy, logout invalidation,
  and offline sync before implementation.

## Consequences

- Installed PWA will not work offline until a later approved phase.
- Theme preference is in-memory only during infrastructure work.
