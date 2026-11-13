# Approval Required (Batch 01)

## No approval needed (already authorized / completed safely)
- Read-only inspection, runtime snapshots, report generation in verified AI_WORKSPACE audit directory.
- Previously approved Hermes default-model correction (completed earlier; backups preserved).

## Requires explicit user approval before execution
| ID | Action | Why approval required | Risk |
|---|---|---|---|
| A1 | Hermes fallback chain config / provider additions / model alias changes | Modifies `~/.hermes/config.yaml` behavior | Misrouting, cost, degraded reliability |
| A2 | Any `.env` / credential / token / auth changes | Security-sensitive | Secret exposure, lockout, billing |
| A3 | Service stop/start/restart (Hermes/Honcho/Postgres/Docker apps) | Runtime impact; may affect active work | Data loss, downtime |
| A4 | Docker/PostgreSQL removal or container/port/data changes | Existing apps may depend; master doc allows inspection not blind removal | Outage/data loss |
| A5 | Workspace migration, path rewrites, symlinks, moving JARVIS/AJ/HELIX/DB/venv/browser profiles | Active state + uncommitted work | Breakage, data loss |
| A6 | Database schema/migration, writes, deletions, cleanup, VACUUM on production DBs | Mutating/potentially destructive | Irreversible data impact |
| A7 | Desktop/browser automation UI tests (click/type) | Can trigger real side effects in user environment | Unintended actions |
| A8 | Paid/billable API tests or additional provider requests beyond explicit approval | Cost/rate limits | Unexpected charges |
| A9 | Git commit/push/merge/rebase/reset/clean/force operations | History/worktree risk | Loss of work |
| A10 | Deleting files/backups/containers/volumes/models | Destructive/irreversible | Permanent loss |
| A11 | Package installs/updates/downloads (esp. large models) | Environment/disk impact | Breakage, disk exhaustion |
