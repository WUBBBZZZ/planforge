# Planforge

Planforge is a modular, self-hosted personal planning platform. It acts as a
configurable planning engine rather than a rigid planner: routines,
maintenance schedules, backlogs, appointments, and daily checklists are all
driven by user-configurable behavior rather than hard-coded rules.

> **Status: early development.** The repository currently contains project
> scaffolding only. Application code will arrive in small, reviewed phases.

## Planned capabilities

- One-time tasks, backlog items, and appointments
- Recurring routines with generated occurrences
- Long-term maintenance definitions and rescheduling
- Weekly targets, monthly and weekly planning views
- Lightweight daily checklists with completion history
- Configurable missed-item and rollover behavior
- Custom visibility in Today, Week, and Month views
- Themes, layout settings, and user preferences
- Data export, backup, and completion-history analytics
- Installable Progressive Web App (desktop and phone)

## Architecture

- **Monorepo** with a Python backend and a TypeScript frontend
- **Backend:** FastAPI, SQLAlchemy, SQLite during development with a clear
  migration path to PostgreSQL
- **Frontend:** React + TypeScript, installable PWA, typed against the
  backend's OpenAPI schema
- **Local-first and self-hosted:** no cloud service; each installation is
  fully independent. Development services bind to `127.0.0.1` by default.
- **Single-user first**, with data structures designed to be multi-user-ready

```
planforge/
├── backend/    # FastAPI application (Python)
├── frontend/   # React + TypeScript PWA
└── docs/       # Architecture notes and decision records
```

## Configuration

Planner behavior is configured through the application UI. Environment
variables are used only for developer, deployment, and secret configuration;
see `.env.example` for the template. Real `.env` files, databases, and
backups are never committed to this repository.

## License

[MIT](LICENSE)
