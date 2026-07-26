# Planforge

Self-hosted personal planning platform (FastAPI + React + SQLite).

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

Open `http://127.0.0.1:5173` for the Week view. Today is at `/today`.

Copy `.env.example` to `.env` for local configuration. Real secrets and
databases are never committed.

## License

[MIT](LICENSE)
