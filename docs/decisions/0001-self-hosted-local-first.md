# ADR 0001: Self-hosted, local-first architecture

## Status

Accepted

## Context

Planforge must be runnable by anyone who clones the public repository without
depending on a central service operated by the author.

## Decision

- Each installation is fully independent (local database, local configuration).
- No mandatory cloud backend; no telemetry to the author.
- Development and default runtime bind to loopback (`127.0.0.1`).

## Consequences

- Users are responsible for backups and updates on their own machines.
- Cross-device access requires explicit later phases (Tailscale Serve, HTTPS,
  authentication) with security review.
