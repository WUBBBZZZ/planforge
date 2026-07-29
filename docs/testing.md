# Testing

## Backend (pytest)

Location: `backend/tests/`

```powershell
cd backend
.\.venv\Scripts\pytest.exe
```

Coverage is enforced at **80%** (`--cov-fail-under=80` in `pyproject.toml`).

### Suites

| Area | Location | Coverage |
|------|----------|----------|
| Domain (dates, intervals, scheduling) | `tests/domain/` | Calendar rules, DST |
| Services | `tests/services/` | Business logic |
| API | `tests/api/` | All routers |
| E2E workflows | `tests/test_e2e_workflows.py` | Cross-entity flows |
| Migrations | `tests/test_migrations.py` | Fresh DB + upgrade from 0007 |
| Integration | `tests/test_appointment_maintenance_integration.py` | Linked appointments |
| Recurrence edges | `tests/test_recurrence_edge_cases.py` | Month-end, biweekly |
| Backup | `tests/test_backup_verification.py` | SQLite backup API |
| Router smoke | `tests/test_api_router_smoke.py` | Every router responds |

## Frontend (Vitest + Testing Library)

Location: `frontend/src/**/*.test.ts(x)`

```powershell
cd frontend
npm run test
npm run test:coverage
```

### Suites

| Area | Location |
|------|----------|
| Components | `src/components/*.test.tsx` |
| Pages | `src/pages/*.test.tsx` |
| API client errors | `src/lib/apiClient.test.ts` |
| Accessibility | `src/test/accessibility.test.tsx` |

Coverage thresholds are configured in `vite.config.ts` (realistic baselines for
the current UI surface).

## CI

GitHub Actions runs the same checks on every push and pull request. See
[tooling.md](tooling.md) for the job matrix.

## Fabricated data

Tests, fixtures, and examples use obviously fake content only (e.g. "Dentist
demo", "Water demo plants"). Never use real personal data in the repository.

## Regenerating OpenAPI types

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\export_openapi.py

cd ..\frontend
npm run generate:api-types
```

Commit both `frontend/openapi/openapi.json` and `frontend/src/api/schema.d.ts`
when API shapes change.
