# Planforge

Planforge is a modular, self-hosted personal planning platform. It acts as a
configurable planning engine rather than a rigid planner: routines,
maintenance schedules, backlogs, appointments, and daily checklists are driven
by user-configurable behavior rather than hard-coded rules.

> **Status:** infrastructure scaffolding is implemented. Planner features are
> planned and not yet available.

## Implemented

- Monorepo layout with `backend/` and `frontend/`
- FastAPI backend skeleton with `/api/health`, settings, logging, SQLAlchemy,
  and Alembic scaffolding (SQLite, loopback-only defaults)
- React + TypeScript frontend skeleton with accessible shell, theme foundations,
  generic UI primitives, and backend health display
- Web app manifest and installability metadata (**no service worker yet**)
- Pre-commit hooks with secret scanning (gitleaks)
- GitHub Actions CI and Dependabot configuration
- Documentation and architecture decision records (ADRs)

## In progress

- Product requirements and domain discovery ([`docs/requirements/`](docs/requirements/))
- ADR 0006 date/time design — **accepted** ([`docs/decisions/0006-date-time-design.md`](docs/decisions/0006-date-time-design.md))
- Expanded UI primitives and dev component gallery (`/dev/components`)

## Planned

- Planner entities, workflows, and configurable policies
- Authentication (security gate; architecture not yet chosen)
- Service workers, offline behavior, and browser storage (security gate)
- Deployment packaging and optional Tailscale Serve access (security gates)
- Data export/import UI, analytics, and backup restore UI

## Architecture

- **Monorepo:** Python backend + TypeScript frontend
- **Backend:** FastAPI, SQLAlchemy, SQLite (default supported database)
- **Frontend:** React, Vite, installable PWA metadata (offline deferred)
- **Local-first:** each installation is independent; dev services bind to
  `127.0.0.1` by default

```
planforge/
├── backend/    # FastAPI application (Python 3.14)
├── frontend/   # React + TypeScript UI
└── docs/       # Setup, security, testing, ADRs
```

## Quick start (Windows / PowerShell)

### Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\uvicorn.exe planforge.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` for the development status screen, or
`http://127.0.0.1:5173/dev/components` for the UI primitive gallery.

See [docs/development-setup.md](docs/development-setup.md) for full details.

## Configuration

Planner behavior will be configured through the application UI. Environment
variables are for developer/deployment concerns only; see `.env.example`.
Real `.env` files, databases, and backups are never committed.

## License

[MIT](LICENSE)
