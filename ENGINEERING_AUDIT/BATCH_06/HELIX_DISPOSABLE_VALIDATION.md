# HELIX Disposable Validation (Workstream D)

**Disposable copy (A4, non-destructive):** `ENGINEERING_AUDIT/BATCH_06/helix_home_disposable/` (copy of `/home/abubakargcx/helix`, excluded `ui/node_modules`, pycache, pytest cache, `*.pyc`).
**Originals untouched:** `/home/abubakargcx/helix`, `AI_WORKSPACE/helix`, `backup/HELIX-backup-20261109T211343Z-batch03`. **Not deployed, not connected to live services, no destructive commands.**

## 1. Structural inspection (STATIC EVIDENCE)
| Area | Finding |
|---|---|
| Entry points | `bridge/bridge_ws.py`, `bridge/helix_desktop.py`, `tools/live_server.py` present; `bridge/server.py` absent (deleted by WIP) |
| UI | `ui/package.json`, `ui/build.js`, `ui/helix-ui.html`, `ui/src/{index.html,js,style.css}` present; legacy `ui/agent-town|console|shell|voice-core|world-monitor` pages absent (deleted by WIP) |
| Spec/docs | `docs/HELIX_BUILD_SPEC.md` present; `docs/AGENT_ARCHITECTURE.md`, `docs/PACKAGING_PLAN.md`, `docs/ADD_AN_AGENT.md`, `docs/PROGRESS.md` present |
| Tooling | `tools/lms_client.py`, `selfcheck.py`, live/voice tools present; 13 legacy `check-*/gesture/geometry/probe` diagnostics absent (deleted by WIP) |
| Packaging | `install.sh`, `uninstall.sh`, `deploy/helix-gesture.service` (deleted in WIP; workspace branch also deletes it) |
| Dependency consistency | Not executed (no install/build). `ui/node_modules` excluded; no Python dependency manifest observed |

## 2. Consolidation verification (new, decisive)
The disposable copy was compared against `AI_WORKSPACE/helix` HEAD; full artifacts in `helix_wip_consolidation_map.txt` and `helix_tree_divergence.txt`.

| Evidence | Result |
|---|---|
| Git ancestry | `e8a64cf` (home) **is an ancestor** of `99c7a38` (workspace); home has **0** commits the workspace lacks; workspace has 3 |
| Commit change set | `e8a64cf..99c7a38` = 25 added / 24 deleted / 9 modified |
| WIP additions | **17 of 19** meaningful non-deleted WIP entries are byte-identical in the workspace tree; the other 2 (`ui/src/`, `.gitignore`) exist but are **newer** in the workspace; `ui/node_modules/` is build cache |
| WIP deletions | **22 of 22** deletions are committed identically on the workspace branch |
| Genuine divergence | only `ui/src/` and `.gitignore` (workspace newer); `ui/node_modules/` is build cache |

**Conclusion:** the home tree's WIP is **already consolidated** into `audit/consolidation-2026-11-06`; it is a stale pre-consolidation working tree, not a competing line.

## 3. Does the WIP tree satisfy the documented architecture?
| Criterion | Verdict |
|---|---|
| Architecture artifacts present per spec (desktop/bridge/voice/UI/LMS/delegation docs) | **PARTIAL/VERIFIED structurally** |
| Entrypoints resolvable without the deleted legacy surfaces | **LIKELY** — `bridge_ws.py` + `helix_desktop.py` + `ui/src` are the replacements; the deleted `ui/*` pages and `bridge/server.py` have no remaining referents in the copy (static check only) |
| Build/run proven | **NO** — no install/build/import execution performed (no manifest; out of non-destructive scope) |
| End-to-end spec compliance | **UNVERIFIED** |
| Active-runtime equivalence | **Differs**: active `helix-live` runs the workspace tree, whose `tools/live_server.py`, `live_tts.py`, `helix_voice.py`, `check-live.py` are **newer** than the home copy (`07a2522`, `99c7a38`) |

**Assessment (supersedes earlier wording):** the WIP tree is an **incomplete-but-coherent refactor snapshot whose intent was carried into the audit branch**; it is **not** an incomplete refactor that needs rescuing, and it is **not** a production-ready replacement. The workspace branch is the better artifact on every measured axis.

## 4. Recommended next validation (approval-gated, still read-only)
1. On a fresh disposable copy: static import/AST check of `bridge_ws.py`, `helix_desktop.py`, `tools/live_server.py`.
2. Diff review of the two residual home-only edits (`ui/src/`, `.gitignore`) to confirm they are superseded.
3. UI build dry-run **only** if dependency installation is explicitly authorized (currently not).
No connection to live Hermes/Honcho/services; no deployment.
