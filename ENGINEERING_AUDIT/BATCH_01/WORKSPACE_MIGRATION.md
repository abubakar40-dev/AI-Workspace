# AI_WORKSPACE & Migration Verification (Batch 01, partial)

**Scope:** read-only inspection. Full checksum/metadata comparison across active repos, backups, venvs, DB/WAL/SHM, browser profiles, and runtime data **not completed**.

## Verified facts
- AI_WORKSPACE mount present: `/run/media/abubakargcx/My Drive/AI_WORKSPACE` exists; `/run/media/abubakargcx/My Drive` mountpoint (VERIFIED).
- `/home/abubakargcx/JARVIS` is **missing** (VERIFIED). Master doc lists it as a project root; migration state unresolved.
- `/home/abubakargcx/helix` exists as a git repo (`main...origin/main`) with local modifications/deletions/untracked-like worktree changes (OBSERVED, `git status --short` sampled).
- Workspace contains: `AJ/` (not git; AJ pre-Hermes foundation), `honcho_local/` (git, local untracked `honcho_server.py`, `minimal_server.py`), `backup/` including `JARVIS-old-repo-20261106`, `JARVIS-nested-duplicate-20261106`, `Download-old-20261106`, etc.; planning docs `AJ_Ecosystem_Planning_Documentation_v2_fixed/AJ_MASTER_PROJECT_CONTEXT.md` (OBSERVED).
- Honcho running from workspace path `AI_WORKSPACE/honcho_local` via `~/.hermes/venv-honcho` (OBSERVED process cmdline).

## Migration completeness matrix (partial)
| Component | Home/original | Workspace/backup evidence | Status |
|---|---|---|---|
| JARVIS (canonical) | `/home/abubakargcx/JARVIS` missing | `AI_WORKSPACE/AJ/` (different codebase name/purpose?) + JARVIS backups in `backup/` | **UNVERIFIED / HIGH RISK**: active canonical copy not identified |
| HELIX | `/home/abubakargcx/helix` present (dirty) | backup presence not fully compared | **INCOMPLETE COPY STATUS** |
| Hermes | `~/.hermes` present | workspace may contain Hermes-related dirs (not fully inventoried) | **PARTIAL** |
| Honcho | running service | source in `AI_WORKSPACE/honcho_local` | **OBSERVED active from workspace** |
| Obsidian/God's Eye View/supporting tools | not verified | workspace listing suggests possible related dirs; not audited | **UNVERIFIED** |
| Venvs/DBs/WAL/browser profiles/creds | not verified | backups contain venvs/DB-like dirs; active paths unknown | **UNVERIFIED** |

## Broken path / dependency risks (INFERRED/UNVERIFIED)
- Any service/config hardcoded to `/home/abubakargcx/JARVIS` may fail (path missing). Not scanned.
- Active processes may still use old/home/workspace paths inconsistently. Not mapped.
- SQLite WAL/SHM and browser profiles in backups/copies require special handling; comparing active DBs by checksum can be unsafe/misleading.

## Safe migration sequence (RECOMMENDED, requires approval before execution)
1. Freeze writes only with explicit coordination (no stop/restart without approval). Identify canonical active copy for JARVIS/AJ and HELIX.
2. Inventory active PIDs, open files, systemd units, cron, shell aliases, and absolute paths in configs/scripts.
3. Metadata-first comparison (sizes, mtimes, git HEAD/status, manifest hashes) excluding volatile DB/WAL/browser runtime where appropriate; targeted integrity checks for static assets.
4. Backups verified + recovery tested before path changes. 3-2-1 per master doc.
5. Prefer explicit config/path abstraction or controlled symlink transition only after dependency map and GREEN SIGNAL for destructive/path-changing steps.

## Gaps
No checksum manifest generated; no symlink audit; no hardcoded-path scan; no runtime-open-file map; no DB/browser-profile/venv validation.
