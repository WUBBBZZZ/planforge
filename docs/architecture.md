# Planforge Architecture

## Overview

Planforge is a local-first, self-hosted planning platform delivered as a
monorepo:

| Component | Stack | Status |
|-----------|-------|--------|
| `backend/` | FastAPI, SQLAlchemy, Alembic, SQLite | Infrastructure skeleton |
| `frontend/` | React, TypeScript, Vite | Infrastructure skeleton |
| `docs/` | ADRs, setup, security | Active |

## Principles

- **End-user program:** planner behavior is configured through the UI, not
  source code or environment variables.
- **Local-first:** each installation is independent; no shared cloud service.
- **Security by default:** loopback binding until authentication; no public
  exposure; secrets only in untracked `.env`.
- **SQLite default:** fully supported for personal self-hosting; portable ORM
  patterns for optional PostgreSQL later.
- **Vertical slices:** features ship end-to-end (domain → persistence → API → UI).
- **Single-user first, multi-user-ready:** UUID keys and ownership columns from
  the start.

## Current API surface

- `GET /api/health` — returns `{"status": "ok"}`

OpenAPI schema: `http://127.0.0.1:8000/openapi.json` when the backend is running.

## Frontend installability

The frontend includes a web app manifest and generic icons for installability
metadata. **No service worker or offline caching** — deferred to a security gate.

## Decision records

See [`decisions/`](decisions/) for numbered ADRs.

## Roadmap alignment

Implemented infrastructure corresponds to Phases 1–2 and partial backend/frontend
skeleton phases. Product requirements, planner logic, authentication, offline
behavior, deployment, and Tailscale access follow later approved phases.
