# Batch 02 — Actions Requiring Explicit Approval

**No fixes were implemented.** The following are proposed only.

## A1 — Safe read-only / low-risk investigation (explicit user OK recommended)
- Full PID/exe/cwd/unit mapping for ports 8000/8765/3200.
- Full diff of `JARVIS-old-repo` vs `JARVIS-nested-duplicate` (read-only; may take I/O time).
- Read HELIX build spec/progress/architecture and compare new bridge/UI entrypoints to deleted ones.
- Inspect `~/.hermes/plugins/honcho` implementation and Hermes Honcho enablement path.
- Metadata-only code/config searches for active AJ/JARVIS/HELIX entrypoints and DB paths.

## A2 — Privileged/sensitive read access (approval required)
- Authorized PostgreSQL 18 admin access to list all DBs/roles/schemas/tables/row counts/timestamps on cluster 5433 (Honcho/others), **metadata only, no sensitive row dumps**.
- Read `pg_hba.conf` and relevant cluster auth settings.
- Firewall/service exposure review with sufficient privileges (read-only).

## A3 — State-changing or operational (GREEN SIGNAL / explicit approval; separate batch)
- Tighten file permissions (e.g., `~/.hermes/honcho.json` 600).
- Bind/firewall changes for 3389/5432/5434/8000/8765.
- Service/container restarts, config edits, DB migrations, installs, git cleanup/restore/commit.
- Any deletion, move, merge, rename, or dedupe of JARVIS backups/HELIX files.

## A4 — Backup/snapshot operations (approval required)
- Non-destructive backup copy of `/home/abubakargcx/helix` including untracked files to timestamped backup.
- Docker volume / PG18 data-dir backup or restore tests in isolated environment.

## User decisions (cannot be safely inferred)
- Canonical active source: AJ control plane vs legacy JARVIS app vs hybrid; which directory becomes authoritative.
- HELIX refactor intent: keep/restore old bridge+UI vs complete new `bridge_ws`/desktop/`ui/src` path.
- Intended exposure of RDP and Dental Lounge DB ports.
- Memory ownership contract adoption (AJ canonical store boundaries; Honcho/Hermes roles).
