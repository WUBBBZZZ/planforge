# Testing

## Backend (pytest)

Location: `backend/tests/`

```powershell
cd backend
.\.venv\Scripts\pytest.exe
```

Current mechanical tests cover:

- Application factory construction
- Default loopback configuration
- Environment overrides with fabricated values
- `/api/health` response

Behavioral planner tests will be written against specs from the requirements
phase; core logic is implemented by the project owner.

## Frontend (Vitest + Testing Library)

Location: `frontend/src/**/*.test.tsx`

```powershell
cd frontend
npm run test
```

Current mechanical tests cover shared primitives (Button, EmptyState).

## CI

GitHub Actions runs the same checks on every push and pull request. Reproduce
failures locally using the commands in [tooling.md](tooling.md).

## Fabricated data

Tests, fixtures, and examples use obviously fake content only (e.g. "Alex
Example", "Water the plants"). Never use real personal data in the repository.

## Definition of done

See the roadmap: features need acceptance criteria, accessibility, passing
checks, and security review when applicable.
