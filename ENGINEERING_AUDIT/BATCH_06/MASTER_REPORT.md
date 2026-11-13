# Batch 06 Master Report — Canonical Decision Package & Controlled Memory Validation

**Project:** AJ / JARVIS / HELIX / Hermes / Honcho  
**Workspace:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`  
**Mode:** A1 read-only, A2 metadata-only, A4 disposable copy (`BATCH_06/helix_home_disposable/`). **No unauthorized mutations.**

## Workstream outcomes
| Workstream | Outcome |
|---|---|
| A. Hermes→Honcho controlled validation | **TEST INCONCLUSIVE / PARTIALLY VERIFIED.** Pre/post-equivalent A2 metadata: `2/1/0/0/0`. Observed synthetic `HONCHO_TEST_OK` turn was **misrouted** to Honcho as LLM provider (`base_url=http://localhost:8123`, 404) — invalid writer test. No new valid delta test executed (safety/routing/paid-call/DB-write approval boundary). |
| B. AJ/JARVIS canonical decision package | Completed. AJ recommended as control-plane target; JARVIS independent role; backups preserved source-equivalent (filtered); separate repos. Decisions labeled **RECOMMENDED/USER DECISION REQUIRED**. |
| C. HELIX canonical tree decision | Completed, **corrected by verified git ancestry**: `e8a64cf` (home `main`) is an **ancestor** of `99c7a38` (workspace `audit/consolidation-2026-11-06`); home has **0** commits the workspace lacks. The audit branch **already commits the home WIP** (17/19 identical files, 22/22 deletions matched; only `ui/src` and `.gitignore` newer in workspace). Conclusion: workspace tree is the **linear successor**, not a divergent line; home tree is a stale pre-consolidation working tree. Canonical line recommended = `AI_WORKSPACE/helix`. No merge performed. |
| D. HELIX disposable validation | Completed in `BATCH_06/helix_home_disposable/`. Contains spec/bridge_ws/desktop/UI/tools; build/import **not executed**; end-to-end spec compliance **UNVERIFIED**. Consolidation map proves no WIP content is lost. Originals/backup untouched. |
| E. Canonical memory decision | Completed. **Candidate A recommended:** AJ raw-first canonical; Honcho adapter/index/derived, **not canonical now** (writer unproven, 0 messages). |
| F. Exposure policy decision package | Completed. Local ecosystem services mostly localhost-bound; 8000/3389/5432/5434/8765 require intent/auth review; `UNKNOWN — DO NOT ASSUME SAFE`. |
| G. Canonical architecture v1 | Completed (`AJ_ECOSYSTEM_CANONICAL_ARCHITECTURE_v1.md`) with boundaries and ASCII diagram. |
| H. Implementation gate | Completed. **NOT READY** broad; limited foundation not granted. |

## Verified facts (new in B06)
- **HELIX is not a fork:** `e8a64cf` is an ancestor of `99c7a38`; the workspace branch commits the home WIP (17/19 files byte-identical, 22/22 deletions matched). Only `ui/src/` and `.gitignore` differ (workspace newer). Artifacts: `helix_tree_divergence.txt`, `helix_wip_consolidation_map.txt`.
- **Honcho write gates:** plugin hook is `on_session_end` + memory-provider registration; `saveMessages` default **true**, `writeFrequency` **async**. Persistence is on by default and flushes asynchronously.
- **Compliant writer test is currently impossible without a service change:** no local LLM is listening (11434/1234/8080/5000 empty; ollama server down) and the only configured provider is paid OpenRouter. Launch flags exist (`--provider/--model/--base-url`) but there is nothing zero-cost to target.
- **AJ is not runnable as-is:** no `pyproject.toml`/`requirements*.txt`, no venv, `pytest` absent, no `main.py`/`__main__.py`/`cli.py` — 6 test suites exist but could not be executed.
- Honcho message/conclusion counts remain **0** (A2 metadata-only).
- A real local Hermes turn with synthetic content `HONCHO_TEST_OK` hit Honcho as **LLM provider endpoint** (404), evidencing misrouting and invalidating that path as a writer proof.
- `helix_home_disposable` copy exists for validation only; originals/verified backup untouched.

## Decisions recommended
- AJ canonical control-plane direction (`AI_WORKSPACE/AJ` foundation), separate projects. JARVIS independent, backups preserved. **HELIX: one lineage — canonical line = `AI_WORKSPACE/helix` @ `99c7a38`; home tree is archival (WIP already consolidated)**; no merge. Memory target = AJ raw-first canonical + Honcho adapter/index (not canonical now). Externally bindable services need intent/auth decisions.

## User decisions required
AJ runtime/source & activation scope; JARVIS scope/source; HELIX canonical working line; memory direction ratification; exposure intent (8000/3389/5432/5434/8765); approval for a valid, safe Hermes→Honcho metadata-delta test plan.

## Implementation gate
**`NOT READY`**

## Next engineering phase
**Batch 07 — Decision Ratification & Limited Foundation Plan (gated):** capture explicit decisions, run approved correctly routed synthetic Honcho writer validation (if safe), and draft A3-scoped limited foundation plan (AJ entrypoint skeleton, memory/audit/task/permission contracts) — no implementation without A3/GREEN SIGNAL.
