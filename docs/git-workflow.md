# Git workflow

Planforge uses feature branches, conventional commits, pull requests for
review, and pre-commit hooks before every commit.

## Branching

- `main` — stable infrastructure and approved features
- `feature/<short-description>` — short-lived branches for a single change

## Commit messages

Use concise conventional commits:

- `feat: add health endpoint`
- `fix: correct SQLite path default`
- `docs: explain pre-commit hooks`
- `chore: configure Dependabot`

## Typical flow (PowerShell)

```powershell
git checkout -b feature/example-change
# edit files
py -m pre_commit run --all-files
git add -A
git commit -m "feat: describe the change"
git push -u origin feature/example-change
gh pr create --title "Title" --body "Summary and test plan"
```

## Pull requests

Use the template at [`.github/pull_request_template.md`](../.github/pull_request_template.md).
Confirm:

- Pre-commit passed locally
- No secrets or personal data
- CI checks pass

## Branch protection (later)

Branch protection on `main` is configured **after** CI job names exist and
have run at least once on GitHub. Intended required checks:

- `backend / format`
- `backend / lint`
- `backend / typecheck`
- `backend / test`
- `frontend / format`
- `frontend / lint`
- `frontend / typecheck`
- `frontend / test`
- `frontend / build`

## Never

- Force-push to `main`
- Commit `.env`, databases, backups, or keys
- Skip secret scanning to "make CI pass"
- Rewrite published history without explicit approval
