# Security

Planforge is self-hosted and local-first. Reduced exposure does not remove the
need for careful defaults.

## Pre-authentication rule (active now)

Until authentication (Phase 9) is complete and approved:

- Services bind to **127.0.0.1** only
- **Fabricated data only** in development and documentation
- **No phone or remote access**
- **No LAN, tailnet, or public internet exposure**
- No wildcard CORS, no service worker, no browser persistence for planner data

## Protected assets

- Personal tasks, appointments, routines, and completion history
- Session tokens and credentials (when authentication exists)
- Database files and backups
- Environment secrets (`.env`)

## Repository rules

Never commit:

- `.env` (only `.env.example` with placeholders)
- Database files, backups, private keys, certificates
- Real personal data, emails, private IPs, or device names

Pre-commit runs **gitleaks** and **detect-private-key** on every commit.

## Logging

Backend logging must not include request bodies, passwords, tokens, cookies,
session identifiers, planner content, or personal data.

## Authentication (deferred)

Authentication architecture is **not chosen yet**. A future security gate will
compare conservative options. Password hashing will use a maintained
Argon2-capable library; **pwdlib** is the initial candidate to evaluate.

## Offline and service workers (deferred)

Service workers, offline caching, and browser storage are deferred to a
dedicated security gate. The frontend currently ships manifest/installability
metadata only.

## Network exposure

- Development: loopback only (`127.0.0.1`)
- **Phone access: not enabled** in the current phase
- Deployment: application and database ports must not be reachable from LAN or
  public internet
- Future phone access: only via approved **Tailscale Serve** on the private
  tailnet — **Funnel and router port forwarding are prohibited**

## Database backup

Manual verified backups are documented in [backup.md](backup.md). Arbitrary
file import is not implemented.

## If a secret is committed

1. Assume it is compromised — rotate immediately
2. Remove it from the working tree
3. Do not push; seek history cleanup before publication if already committed
4. Re-run `py -m pre_commit run --all-files`

## Reporting uncertainty

If a security decision is unclear, document the uncertainty and wait for
explicit approval before implementing.
