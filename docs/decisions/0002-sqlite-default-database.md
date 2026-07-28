# ADR 0002: SQLite as the default database

## Status

Accepted

## Context

Personal self-hosting should be simple to install and operate on a single Windows
PC without container orchestration.

## Decision

- **SQLite is the default, fully supported database** for Planforge.
- SQLAlchemy + Alembic keep migrations portable for optional PostgreSQL later.
- No database container is introduced by default.

## Consequences

- Concurrent write patterns must be designed for SQLite limits until PostgreSQL
  is an explicit opt-in addition.
- Backups are file copies of the SQLite database (see manual backup phase).
