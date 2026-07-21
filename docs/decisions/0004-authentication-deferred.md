# ADR 0004: Authentication deliberately deferred

## Status

Accepted

## Context

Authentication involves password handling, sessions, CSRF, and network exposure
trade-offs that require a dedicated security gate.

## Decision

- No authentication or authorization in infrastructure phases.
- Architecture is **not preselected** (no Passlib/JWT commitment).
- Future phase will compare conservative options; **pwdlib** is the initial
  Argon2-capable candidate to evaluate.
- Separate approval required before implementation.

## Consequences

- Planforge must not be used with real personal data until authentication exists.
- Only fabricated demo data during development.
