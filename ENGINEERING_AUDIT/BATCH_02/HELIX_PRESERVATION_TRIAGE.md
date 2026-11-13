# HELIX Dirty Worktree & Preservation Triage (Workstream E)

**Repo:** `/home/abubakargcx/helix` — **read-only inspection only; no checkout/reset/restore/stash/clean/commit/push**.

## Repository state (VERIFIED)
- Branch: `main...origin/main`. HEAD: `e8a64cf` (2026-10-18, “Repair Helix dispatch and gesture runtime”).
- Tracked diff: **824 insertions / 6648 deletions** across 27 files (E11).
- Modified tracked: `.gitignore`, `bridge/README.md`, `docs/PROGRESS.md`, `docs/VOICE_AUDIO_DIAGNOSTIC.md`, `tools/selfcheck.py`.
- Deleted tracked (high impact): `bridge/server.py`; `deploy/helix-gesture.service`; many `tools/*` check/diagnostic/app/gesture helpers (`audit-geometry.py`, `check-*.py/sh`, `diagnose-voice.py`, `gesture.py`, `helix_app.py`, `measure-layout.py`, `probe-town.py`, `check-orb/talkover` etc.); large `ui/agent-town/index.html`, `ui/console/*` (`index.html`, `orbScene.js`, `town.js`), `ui/shell/index.html`, `ui/voice-core/*`, `ui/world-monitor/index.html`.
- Untracked: `bridge/bridge_ws.py`, `bridge/helix.desktop`, `bridge/helix_desktop.py`, `docs/ADD_AN_AGENT.md`, `docs/AGENT_ARCHITECTURE.md`, `docs/PACKAGING_PLAN.md`, `install.sh`, `uninstall.sh`, `tools/lms_client.py`, `ui/build.js`, `ui/helix-ui.html`, `ui/package.json`, `ui/package-lock.json`, `ui/src/`, `ui/node_modules/` (likely generated dependencies).

## Evidence-based classification
| File/path | Git state | Related feature | Diff summary (high-level) | Spec/reference | Risk | Confidence |
|---|---|---|---|---|---|---|
| `bridge/server.py` | deleted tracked | bridge/server runtime | -1242 lines (per diffstat) | `bridge/README.md` modified; build/progress docs exist | **High** if active runtime still depends on it | VERIFIED state; intent UNKNOWN |
| `bridge/bridge_ws.py`, `helix_desktop.py` | untracked | bridge/desktop replacement? | new files present | README/architecture docs untracked/modified | Medium-High (untracked work could be lost) | OBSERVED; **INFERRED possible refactor** (not proven) |
| `deploy/helix-gesture.service` | deleted tracked | gesture deployment | -16 lines | systemd/deploy docs? | Medium | VERIFIED; intent UNKNOWN |
| `tools/check-*.py/sh`, `diagnose-voice.py`, `gesture.py`, `helix_app.py` etc. | deleted tracked | diagnostics/gesture/app tooling | large removals | `tools/selfcheck.py` modified (+/−6) | Medium (may reduce operability/debuggability) | VERIFIED; intent UNKNOWN |
| `ui/console/*`, `ui/shell/*`, `ui/voice-core/*`, `ui/world-monitor/*`, `ui/agent-town/*` | deleted tracked | UI/console/voice/world monitor features | major removals (~4k+ lines in UI files) | master doc requires preserving God’s Eye View/real-time news/Books of Eras/research/voice-related capabilities — **current implementation mapping UNVERIFIED** | **High** (feature preservation risk) | VERIFIED deletions; feature impact UNVERIFIED |
| `ui/src/`, `ui/helix-ui.html`, `ui/build.js`, `ui/package*.json` | untracked | new UI build? | new structure | packaging/agent architecture docs untracked | Medium-High (valuable WIP; untracked) | OBSERVED; **INFERRED possible replacement UI** (not proven) |
| `ui/node_modules/` | untracked | dependencies | generated/vendor tree likely | n/a | Low value to preserve as source; **do not delete without approval** | INFERRED generated |
| `docs/PROGRESS.md`, `VOICE_AUDIO_DIAGNOSTIC.md`, `ADD_AN_AGENT.md`, `AGENT_ARCHITECTURE.md`, `PACKAGING_PLAN.md` | modified/untracked | documentation | progress +787 in diffstat; new docs untracked | HELIX build spec/progress refs to locate/read | Medium (knowledge preservation) | VERIFIED/OBSERVED |
| `install.sh`, `uninstall.sh` | untracked | packaging/install | new scripts | packaging plan untracked | Medium; `uninstall.sh` needs caution (no execution) | OBSERVED |
| `tools/lms_client.py` | untracked | LMS integration? | new file | master backlog includes LMS workflows | Medium | OBSERVED |

## Determinations
1. **Features potentially affected:** bridge runtime, gesture deployment/runtime, diagnostics/self-check tooling, console/shell/voice-core/world-monitor/agent-town UI surfaces. God’s Eye View may be served separately by `helix-globe.service` from `AI_WORKSPACE/gods-eye-view` (E07) — **separate from these deleted HELIX UI paths**, but HELIX UI integration impact is UNVERIFIED.
2. **Unique/must-preserve:** all untracked source/docs (`bridge_ws.py`, `helix_desktop.py`, `ui/src`, `ui/*.html/build/package`, new docs, scripts, `tools/lms_client.py`) and all local modifications/deletions represent current work state — **preserve entire worktree as-is**.
3. **Earlier versions:** HEAD `e8a64cf` and remote `origin/main` (if reachable) contain pre-deletion tracked versions; untracked files have **no git backup** evidenced here.
4. **Divergence:** local branch has uncommitted changes; upstream comparison beyond `main...origin/main` status not fully analyzed.
5. **Safe future tests (approval-gated if they touch services/UI/networks):** static import/manifest checks, `tools/selfcheck.py` read/review, isolated unit tests if found, non-mutating build checks in a copy; avoid starting services or external calls without approval.
6. **User clarification needed before any cleanup/restoration:** Is the deletion of `bridge/server.py` and old UI intentional replacement by `bridge_ws.py`/`helix_desktop.py`/`ui/src`? Which UI is canonical? Are `ui/node_modules` and `uninstall.sh` intended? Should deleted diagnostics be restored from HEAD or kept removed?

## Preservation-first recovery strategy (no implementation now)
1. **Immediate:** take a *non-destructive* backup snapshot of `/home/abubakargcx/helix` including untracked files to a new timestamped backup location **only with explicit approval** (copying is write activity outside report dir). Until then, do not touch worktree.
2. **Analysis:** read `docs/HELIX_BUILD_SPEC.md`, `docs/PROGRESS.md`, `AGENT_ARCHITECTURE.md`, `PACKAGING_PLAN.md`, modified `bridge/README.md`, and diffs of key files to determine intent.
3. **Validation plan:** compare expected entrypoints/imports/config refs against new untracked files; run safe tests in an isolated copy.
4. **Any restore/cleanup:** requires explicit file-by-file approval; never `git clean/reset/checkout -- .` blindly.
