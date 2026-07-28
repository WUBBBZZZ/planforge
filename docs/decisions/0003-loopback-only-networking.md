# ADR 0003: Loopback-only default networking

## Status

Accepted

## Context

Until authentication and deployment are reviewed, exposing the API increases
risk without benefit.

## Decision

- Default host: `127.0.0.1`
- Default port: `8000` (backend), `5173` (frontend dev)
- No wildcard CORS; no LAN or public binding during infrastructure phases
- Pre-authentication global rule: no remote, tailnet, or phone access

## Consequences

- Only local browser tabs on the same machine can reach dev services.
- Deployment and Tailscale phases must re-verify binding and reachability.
