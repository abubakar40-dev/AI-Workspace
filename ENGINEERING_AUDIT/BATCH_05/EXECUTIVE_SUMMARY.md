# Batch 05 Executive Summary — Identity, Writer Evidence & Port 8000 Resolution

**Date:** 2026-11-10. **Mode:** A1 read-only; A2 metadata-only Honcho counts (no content); A4 preserved. Elevated **read-only** port inspection approved via UI. No source/config/service/DB/git mutations.

## Resolved
1. **Port 8000 owner (RESOLVED):** PID 973, root, `/usr/sbin/legacy-printer-app server`, system service `legacy-printer-app.service` (enabled/active), CWD `/`, bound `0.0.0.0:8000`/`[::]:8000`. **Not AJ/JARVIS/HELIX/Hermes.** Auth/intent **UNVERIFIED** — `UNKNOWN — DO NOT ASSUME SAFE`.
2. **JARVIS application-source uniqueness (RESOLVED, filtered scope):** excluding venv/browser profile/chat history/caches, backups have **259/259 common source files, 0 unique source files**; only `Jarvis/startup.log` differs (runtime log). Batch 04’s old-only bulk was runtime/artifact-dominated.
3. **HELIX runtime identity clarified:** `helix-live` runs **`AI_WORKSPACE/helix/tools/live_server.py`** (git `99c7a38`, clean). `/home/abubakargcx/helix` is **dirty `e8a64cf`** with preserved WIP/deletions and is **not the active helix-live source**. `helix-globe` runs separately from `AI_WORKSPACE/gods-eye-view`. `jarvis-claude-gateway` is inactive and points to missing `/home/abubakargcx/JARVIS`.

## Still blocked / unresolved
- **Hermes→Honcho runtime writer proof:** plugin has real static write capability (`sync_turn` → add/save/flush path, config gates) but **no verified runtime load/invocation/persistence**. A2 metadata still `messages=0, conclusions=0`. Controlled metadata-delta test **not performed** (would require DB writes; needs explicit approval).
- **Canonical AJ/JARVIS runtime/source:** AJ foundation unmapped to active runtime; no active JARVIS runtime; backups source-equivalent but not canonical/active. **Safely unresolved.**
- **HELIX refactor intent/spec equivalence:** specs mapped substantially; split repo states and deleted/untracked replacements leave intent/equivalence **unresolved**.
- **Exposure intent/auth:** 8000 owner known but unverified intent/auth; 3389/5432/5434/8765 remain exposed with unknown intent/auth.

## Architectural consequence
AJ can be treated as the **intended control-plane foundation (static)** but not a verified runtime. Hermes is an active runtime with Honcho **integration capability**, not a proven canonical memory writer. Honcho is a capable local PG18 backend but **not proven canonical ecosystem memory**. HELIX’s active live proxy currently comes from `AI_WORKSPACE/helix`; the home HELIX worktree is preserved WIP/refactor state requiring explicit decisions.

## Implementation status
**`NOT READY`** (broad implementation). Not yet `READY FOR LIMITED FOUNDATION WORK` without explicit AJ source/runtime decision + memory ownership/writer-evidence path.

## Next batch
**Batch 06 — Canonical Decisions & Controlled Writer Validation (decision-gated):** (1) user decisions: AJ canonical runtime/source role, HELIX canonical working tree/intent, exposure intent; (2) if approved, isolated Hermes→Honcho metadata-delta test (synthetic, no content) + deeper Hermes core hook trace; (3) disposable-copy HELIX spec compliance checks. A3/GREEN SIGNAL required for any mutations/hardening/restores.
