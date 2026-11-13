# HELIX Feature Intent & Recovery (Workstream C2)

**Sources:** Batch 03 verified backup (A4), SHA256 integrity (D402), Batch 02/03 triage, running services (helix-live 8788, helix-globe 4173). **Not a full `HELIX_BUILD_SPEC.md` compliance audit** (spec referenced but not exhaustively mapped file-by-file here). **No restore/delete/rename/modify performed.**

## C2 classification (evidence-based)
| Feature/area | Classification | Evidence | Recovery option (proposal, not executed) |
|---|---|---|---|
| Bridge runtime (old `bridge/server.py`) | **Deleted from tracked source**; replacement possibly **untracked experimental/new implementation** | deleted tracked; untracked `bridge/bridge_ws.py`, `bridge/helix_desktop.py` preserved in backup | compare old vs new; restore old only if needed and approved |
| Desktop UI/packaging | **Present but unverified/incomplete** | untracked `helix.desktop`, install/uninstall scripts, packaging docs; deleted gesture service unit | map entrypoints; test in disposable copy |
| Old UI surfaces (`ui/console`, `ui/shell`, `ui/voice-core`, `ui/world-monitor`, `ui/agent-town`) | **Deleted from tracked source** | large tracked deletions (Batch 02) | recoverable from git history if required; confirm not superseded |
| New UI/build (`ui/src`, `build.js`, `helix-ui.html`, package files) | **Untracked experimental/active WIP** (preserved) | untracked in repo/backup; node_modules excluded | validate build/runtime; commit strategy requires approval |
| God’s Eye View | **Present and running (separate service path)**; HELIX integration **unverified** | `helix-globe.service` runs `AI_WORKSPACE/gods-eye-view` on 4173 | verify HELIX UI integration points |
| Real-time News / Books of Eras | **Unknown / documented intent not fully mapped** | master context lists capabilities; deleted old UI paths may have hosted them; new WIP not fully mapped | spec-to-code mapping required |
| Voice/live server | **Present and running (proxy)**; end-to-end feature completeness **unverified** | `helix-live.service` runs `helix/tools/live_server.py` on 8788; deleted voice-core UI tracked files | validate browser/UI + proxy flow (safe/approved tests) |
| Browser/desktop automation | **Unknown/present in parts?** | tools deleted; `helix_desktop.py` untracked; not runtime-verified | static review + controlled tests |
| LMS tools | **Present (untracked WIP)** | `tools/lms_client.py` untracked | review/integrate with approval |
| Diagnostics/gesture tooling | **Deleted from tracked source** (partially) | many tools deleted; `selfcheck.py` modified | restore selected tools if needed |
| Deployment infrastructure | **Partially deleted/changed** | `deploy/helix-gesture.service` deleted; OCI launcher script/service active | reconcile intended deployment model |

## Recovery guidance (safe, approval-gated)
1. **Do nothing destructive.** Backup integrity is verified for preserved files (D402).
2. Read `HELIX_BUILD_SPEC.md`, `docs/PROGRESS.md`, `AGENT_ARCHITECTURE.md`, `PACKAGING_PLAN.md`, modified READMEs, and compare new bridge/UI entrypoints to deleted implementations.
3. Create a **disposable analysis/test copy** (separate path, no modification to source/backup) if runtime/build validation is needed later (A4-permitted pattern); obtain approval if it involves services/network/UI automation.
4. Classify each deleted area as “restore from HEAD”, “superseded by untracked replacement”, or “user decision needed”.
5. Only after explicit approval/GREEN SIGNAL: targeted restore/cleanup/commit strategy — never blanket `git checkout/reset/clean`.
