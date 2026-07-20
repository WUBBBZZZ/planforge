# Planforge Architecture

> Early scaffolding document. Sections will be expanded as each phase is
> designed and approved.

## Overview

Planforge is a local-first, self-hosted planning platform delivered as a
monorepo:

- `backend/` — FastAPI (Python), SQLAlchemy ORM, SQLite in development with
  a migration path to PostgreSQL. Exposes a REST API described by OpenAPI.
- `frontend/` — React + TypeScript installable PWA. API client types are
  generated from the backend's OpenAPI schema.

## Principles

- **End-user program:** planner behavior is configured through the UI, never
  through source code, JSON files, or environment variables.
- **Local-first:** each installation is independent; no shared cloud service.
- **Security by default:** services bind to `127.0.0.1`; no public exposure;
  secrets live only in untracked `.env` files.
- **Single-user first, multi-user-ready:** data models carry ownership from
  the start so multi-user support does not require a schema rewrite.

## Decision records

Significant technical decisions are recorded in [`decisions/`](decisions/)
as short Architecture Decision Records (ADRs).
