# Batch 06 Executive Summary — Canonical Decision Package & Controlled Memory Validation

**Date:** 2026-11-10. **Mode:** A1 read-only, A2 metadata-only, A4 disposable copy. **No source/config/service/network/git/DB mutations.** Controlled Hermes→Honcho writer test **not executed** as a valid new delta test (see below).

## Verified
- Honcho metadata unchanged by any validated writer test: `workspaces=2, sessions=1, peers=0, messages=0, conclusions=0` (A2, no content).
- Observed runtime anomaly: synthetic local message `HONCHO_TEST_OK` was routed with `provider=custom base_url=http://localhost:8123` and failed (404); Honcho received chat/API-style requests (404s). **No Honcho message persistence observed**; path invalid for writer validation.
- Hermes Honcho integration remains **static write-capable** (`plugins.enabled` includes honcho; `sync_turn`/save path present) but **runtime writer behavior is TEST INCONCLUSIVE**.
- AJ is the strongest control-plane foundation (static) with no mapped runtime. JARVIS legacy backups are **source-equivalent in filtered scope**; no active runtime.
- **HELIX is one line, not two (corrected):** `e8a64cf` is an **ancestor** of `99c7a38`; the workspace branch `audit/consolidation-2026-11-06` already commits the home WIP (17/19 files byte-identical, all 22 deletions matched; only `ui/src` and `.gitignore` newer). `/home/abubakargcx/helix` is a **stale pre-consolidation working tree**, not a competing development line. Active runtime baseline remains `AI_WORKSPACE/helix`.
- **Honcho write path mechanics:** plugin declares `on_session_end` and registers as memory provider; `saveMessages` defaults **true** with `writeFrequency=async`. Writes require a **completed** turn — which the misrouted 404 turn never produced.
- **Compliant writer test not constructible now:** no local LLM listener exists and the only configured provider is paid OpenRouter → the test is blocked pending approval of a local model or a single authorized paid call.
- **AJ cannot be run or tested as-is:** no packaging manifest, no venv, `pytest` missing, no entrypoint module; 6 test suites exist but were not executed.
- Port 8000 remains non-ecosystem `legacy-printer-app`, exposed, intent/auth unknown.

## Decisions recommended (not executed)
- **AJ:** target canonical control plane (`AI_WORKSPACE/AJ` foundation), separate from JARVIS/HELIX/Hermes; define runtime entrypoint in approved implementation phase. *(RECOMMENDED / USER DECISION REQUIRED)*
- **JARVIS:** independent personal assistant role; preserve both legacy backups read-only; no merge/delete. *(RECOMMENDED)*
- **HELIX:** canonical line = `AI_WORKSPACE/helix` @ `99c7a38` (the home WIP is already committed there); `/home/abubakargcx/helix` becomes an archival pre-consolidation working tree. No merge. *(RECOMMENDED, high confidence; ratification + optional branch rename = USER DECISION)*
- **Memory:** **AJ raw-first canonical target; Honcho as candidate adapter/index/derived service, not canonical now.** *(RECOMMENDED; USER DECISION REQUIRED)*
- **Exposure:** keep ecosystem localhost services local; review/harden externally bindable 8000/3389/5432/5434/8765 per intent/auth (A3 for changes). *(RECOMMENDED)*

## User decisions required
1. AJ canonical runtime/source and first activation scope. 2. JARVIS future scope/source. 3. HELIX canonical working line. 4. Memory direction (Candidate A). 5. Exposure intent for 8000/3389/5432/5434/8765. 6. Approve a safe, correctly routed Hermes→Honcho metadata-delta test plan.

## Implementation gate
**`NOT READY`** (broad). **Not `READY FOR LIMITED FOUNDATION WORK`** until decisions above + valid writer/contract posture + approved first implementation scope are set.

## Next engineering phase
**Batch 07 — Decision Ratification & Limited Foundation Plan (gated):** record explicit user decisions (AJ/JARVIS/HELIX/memory/exposure), then if approved run a correctly routed synthetic Hermes→Honcho metadata-delta validation (no paid calls, no content, explicit residual-record handling), and produce an A3-scoped limited foundation implementation plan (AJ entrypoint/runtime skeleton + memory contract interfaces + audit/permissions wiring) — **no implementation until A3/GREEN SIGNAL for that scope**.
