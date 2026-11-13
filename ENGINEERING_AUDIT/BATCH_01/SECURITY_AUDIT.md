# Security & Permission Audit (Batch 01, partial)

**Constraint:** no secrets exposed; no credential/config/access-control changes.

## Observed surface (read-only)
- Credential-bearing locations exist by design: `~/.hermes/.env`, `~/.hermes/auth.json`, `~/.hermes/honcho.json` (local Honcho key redacted in reports), OmniRush token stores preserved (not read). `.env`/config presence was checked by key names only in prior work.
- Network exposure: some services listen on `0.0.0.0`/`::` (e.g., 5432/5434 via Docker, 8000, 8765, 3389) — ownership, auth, and firewall posture **UNVERIFIED**. Localhost-only services include Honcho 8123, OmniRush 20129, Hermes bridge 3000, several dev/local ports.
- Hermes gateway/bridge run with user account privileges; tool/MCP/skill execution permissions not fully audited.
- Dirty repos/untracked files in backups/workspace increase accidental-secret leakage risk if committed/shared later (INFERRED). No Git remote actions taken.

## Alignment to master doc (target, not verified implemented)
- Distinguish read-only / reversible / consequential operations; consequential actions require authorization. Agent confidence != authorization. Audit logging and centralized permission enforcement required — **implementation status UNVERIFIED** across JARVIS/HELIX/Hermes/AJ.

## P1 recommendations (REQUIRES USER APPROVAL for changes)
1. Inventory all `.env`, token, browser profile, and DB credential files; verify permissions (read-only report).
2. Review externally bound ports/services and auth requirements.
3. Define/verify consequential-action approval gates for messaging, file deletion, account/security changes, deployments, DB mutations, and paid API calls.
4. Ensure logs redact secrets/tokens; add scanning in CI only if approved.
