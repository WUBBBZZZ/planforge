# Tooling

Planforge uses local pre-commit hooks and GitHub Actions for quality and
security checks. This document explains every hook, what runs where, and how
to debug failures.

## Pre-commit hooks

Configuration: [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)

| Hook | Repo | Auto-fixes files? | Purpose |
|------|------|-------------------|---------|
| `trailing-whitespace` | pre-commit-hooks | **Yes** | Removes trailing spaces |
| `end-of-file-fixer` | pre-commit-hooks | **Yes** | Ensures a final newline |
| `check-json` | pre-commit-hooks | No | Validates JSON syntax |
| `check-yaml` | pre-commit-hooks | No | Validates YAML syntax |
| `check-toml` | pre-commit-hooks | No | Validates TOML syntax |
| `check-merge-conflict` | pre-commit-hooks | No | Detects conflict markers |
| `check-added-large-files` | pre-commit-hooks | No | Rejects files > 500 KB |
| `detect-private-key` | pre-commit-hooks | No | Detects private key material |
| `gitleaks` | gitleaks | No | Scans for secrets/credentials |

### Install hooks (PowerShell)

```powershell
py -m pre_commit install
```

This writes Git hook scripts into `.git/hooks/` for this repository only.

### Run all hooks manually

```powershell
py -m pre_commit run --all-files
```

### Debug a failing hook

1. Read the hook output — it names the file and rule that failed.
2. For auto-fix hooks, stage the fixed files and commit again.
3. For gitleaks/private-key failures, **remove the secret from the file** and
   rotate the credential if it was ever real.
4. Re-run `py -m pre_commit run --all-files` until clean.

### Bypass a hook (justified emergencies only)

```powershell
git commit --no-verify -m "message"
```

Use only when a hook is genuinely wrong, not to skip secret scanning. If a
secret was committed, assume it is compromised: rotate it immediately and
remove it from history before pushing.

## GitHub Actions CI

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

### What runs locally vs on GitHub

| Check | Local command | CI job name |
|-------|---------------|-------------|
| Backend format | `ruff format --check .` (in `backend/`) | `backend / format` |
| Backend lint | `ruff check .` | `backend / lint` |
| Backend types | `mypy planforge` | `backend / typecheck` |
| Backend tests | `pytest` | `backend / test` |
| Frontend format | `npm run format:check` (in `frontend/`) | `frontend / format` |
| Frontend lint | `npm run lint` | `frontend / lint` |
| Frontend types | `npm run typecheck` | `frontend / typecheck` |
| Frontend tests | `npm run test` | `frontend / test` |
| Frontend build | `npm run build` | `frontend / build` |

CI jobs skip gracefully with a message when `backend/pyproject.toml` or
`frontend/package.json` is missing. Once a component exists, jobs perform real
validation.

These job names are intended for branch protection after they have run at least
once on GitHub.

## Dependabot

Configuration: [`.github/dependabot.yml`](../.github/dependabot.yml)

- Weekly checks for Python (`/backend`), npm (`/frontend`), and GitHub Actions
- Patch/minor updates grouped to limit PR noise
- Security updates remain enabled; **never auto-merge**

### Reviewing Dependabot PRs

1. Read the changelog/release notes for breaking changes.
2. Check out the branch locally and run the relevant CI commands.
3. Merge only when tests and lint pass; reject updates that introduce
   unmaintained or incompatible dependencies.
