# HELIX Feature Preservation Map (Phase 6 / A1)

**Basis:** HELIX backup verification (B302), Batch 02 triage (E11), running services (B306), and known master-context feature areas. **Not a file-by-file spec compliance audit** against `docs/HELIX_BUILD_SPEC.md` in this pass (spec read depth limited by time/scope); map is evidence-based and conservative.

| Feature/area | Expected/candidate location (spec/common) | Current evidence | Preservation status/risk | Confidence |
|---|---|---|---|---|
| Bridge/runtime | `bridge/server.py` (deleted tracked), `bridge/README.md` modified | Deleted `bridge/server.py`; untracked `bridge/bridge_ws.py`, `bridge/helix_desktop.py` | **High risk/unclear** — possible refactor; old tracked impl deleted, new impl untracked (preserved in backup) | VERIFIED state; intent UNVERIFIED |
| Desktop/packaging | deploy/unit/scripts | deleted `deploy/helix-gesture.service`; untracked `helix.desktop`, `install.sh`, `uninstall.sh`, `docs/PACKAGING_PLAN.md` | Medium — packaging path in flux | PARTIAL |
| Diagnostics/tools/gesture | `tools/*` check/gesture/app scripts (many deleted) | multiple tool scripts deleted; `tools/selfcheck.py` modified; untracked `tools/lms_client.py` | Medium — operability/debug features may be reduced/relocated | VERIFIED |
| UI console/shell/voice-core/world-monitor/agent-town (old paths) | `ui/console/*`, `ui/shell/*`, `ui/voice-core/*`, `ui/world-monitor/*`, `ui/agent-town/*` | large tracked deletions | **High** if features were only here | VERIFIED deletions |
| New UI/build path | `ui/src`, `ui/build.js`, `ui/helix-ui.html`, `ui/package*.json` | untracked (preserved in backup); `ui/node_modules` excluded as generated | Potential replacement WIP — **must preserve** | OBSERVED |
| God’s Eye View | HELIX UI integration and/or separate service | `helix-globe.service` running from `AI_WORKSPACE/gods-eye-view` on 4173 (separate repo/path) | Service path appears active; HELIX-integration impact UNVERIFIED | VERIFIED service; integration PARTIAL |
| Helix live voice/proxy | `tools/live_server.py` | `helix-live.service` active, PID 10326, serves 8788; references `JARVIS_ROOT` env path | Runtime present; config path dependency UNVERIFIED | VERIFIED |
| Real-time News / Books of Eras / other spec features | per `HELIX_BUILD_SPEC.md`/docs | `docs/PROGRESS.md` modified (+787), new architecture/docs untracked; file-by-file feature mapping not completed | **UNVERIFIED** — preserve all and map against spec next | UNVERIFIED |
| OCI A1 launcher | `tools/oci-a1-launch.sh` | `oci-a1-launch.service` active (16392) | Running from HELIX path (observed) | OBSERVED |

## Preservation priorities
1. **Highest:** untracked source/WIP in backup (`bridge_ws.py`, `helix_desktop.py`, `ui/src`, new docs/scripts, `tools/lms_client.py`).
2. **High:** ability to restore deleted tracked files from git history if needed (`bridge/server.py`, old UI/tools/deploy files) — backup contains current dirty state; git history remains in `.git`.
3. **Clarify before restore/cleanup:** intended canonical bridge/UI/feature set, and whether deletions are completed migration.

No files were restored/removed/renamed/modified.
