# Development setup (Windows 11)

All commands use **PowerShell**. Planforge binds to `127.0.0.1` during
development. Do not expose services to the LAN or internet until approved
security phases are complete.

## Prerequisites

- Python 3.14 via `py` launcher (verified compatible with backend dependencies)
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
npm run build
```

### OpenAPI type generation

Requires the backend running at `127.0.0.1:8000`:

```powershell
npm run generate:api-types
```

## Fabricated data only

Until authentication and product features exist, use demo/fabricated data
only. Do not enter real personal tasks or appointments into development
databases that may appear in local backups.

## Python version note

Backend dependencies were verified on **Python 3.14.2** during infrastructure
setup. If a future dependency drops 3.14 support, record the incompatibility
in an ADR before changing the supported version.
