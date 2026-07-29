# Development setup (Windows 11)

All commands use **PowerShell**. Planforge binds to `127.0.0.1` during
development. Do not expose services to the LAN or internet until approved
security phases are complete. **Phone access is not enabled.**

## Prerequisites

- Python 3.14 via `py` launcher
- Node.js 24 LTS (`node`, `npm`)
- Git 2.53+
- pre-commit 4.6+ (`py -m pre_commit`)

## Clone and hooks

```powershell
git clone https://github.com/WUBBBZZZ/planforge.git
cd planforge
py -m pre_commit install
py -m pre_commit run --all-files
```

## Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy ..\.env.example ..\.env
```

Reproducible installs from the lock file:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
```

Regenerate the lock after dependency changes:

```powershell
..\scripts\lock-python-deps.ps1
```

Start the API (loopback only):

```powershell
.\.venv\Scripts\uvicorn.exe planforge.main:app --host 127.0.0.1 --port 8000
```

Health check: `http://127.0.0.1:8000/api/health`

### Backend validation

```powershell
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\mypy.exe planforge
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\pip-audit.exe
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The dev server proxies `/api` to the backend.

### Frontend validation

```powershell
npm run format:check
npm run lint
npm run typecheck
npm run test
npm run test:coverage
npm run build
npm audit --audit-level=high
```

### OpenAPI type generation

No running server required — uses the committed schema:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\export_openapi.py

cd ..\frontend
npm run generate:api-types
```

## Backup (manual)

```powershell
.\scripts\backup-sqlite.ps1
```

See [backup.md](backup.md).

## Fabricated data only

Use demo/fabricated data only in development databases and screenshots.
