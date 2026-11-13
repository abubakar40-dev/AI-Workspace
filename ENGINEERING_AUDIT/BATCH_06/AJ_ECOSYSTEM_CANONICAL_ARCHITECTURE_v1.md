# AJ Ecosystem Canonical Architecture v1 (Proposed, Evidence-Grounded)

**Labels:** recommendations/decisions marked `RECOMMENDED` or `USER DECISION REQUIRED` unless `EVIDENCE-ESTABLISHED`. No implementation performed.

## 1. Control plane — AJ (`RECOMMENDED / USER DECISION REQUIRED`)
- **Role:** central manager, governance, orchestration, policy, task lifecycle, canonical memory ownership (target).
- **Source candidate:** `AI_WORKSPACE/AJ` foundation (EVIDENCE-ESTABLISHED static). **Runtime not mapped** — activation/entrypoint is a gated implementation task.
- **Boundaries:** AJ coordinates; does not absorb JARVIS/HELIX/Hermes codebases.

## 2. Personal assistant — JARVIS (`RECOMMENDED`)
- **Role:** personal-facing assistant agent with independent identity/repository boundary.
- **Current state:** legacy backups source-equivalent in filtered scope; no active runtime; missing `/home/abubakargcx/JARVIS` path references. Preserve backups; do not merge.

## 3. Advanced execution — HELIX (`RECOMMENDED`)
- **Role:** advanced execution agent/UI/desktop/voice/tool integration (per spec intent), independent project.
- **Current runtime reality (EVIDENCE-ESTABLISHED):** `helix-live.service` uses `AI_WORKSPACE/helix/tools/live_server.py` (clean `99c7a38` on `audit/consolidation-2026-11-06`). That branch **is the successor** of `/home/abubakargcx/helix` (`e8a64cf` is its ancestor; home WIP is already committed there) — so `/home/abubakargcx/helix` is an archival pre-consolidation working tree, **not** a second development line. `helix-globe` is a separate app (`gods-eye-view`).
- **Strategy:** single canonical line (`AI_WORKSPACE/helix`); home tree archived read-only; branch promotion/renaming is an A3 git action.

## 4. Workflow/skill runtime — Hermes (`EVIDENCE-ESTABLISHED` active runtime)
- **Role:** reusable workflow/skill execution runtime and messaging gateway integrations.
- **Memory boundary:** Honcho plugin capability present but runtime writer **TEST INCONCLUSIVE**; Hermes must not be treated as canonical memory owner.

## 5. Memory (`RECOMMENDED / USER DECISION REQUIRED`)
- **Target:** **AJ raw-first canonical** (append-oriented raw events/conversations/tasks, provenance/timestamps) with AJ-governed adapters.
- **Honcho:** candidate **adapter/index/derived-memory service** (PG18 backend healthy, schema capable), **not canonical now** (no verified writer flow, 0 messages/conclusions observed).
- **Layers:** raw canonical store → derived summaries (linked to raw IDs) → rebuildable retrieval/vector indexes.

## 6. Provider layer
- Provider-independent adapters/router. Hermes currently verified on OpenRouter default baseline (prior batches). AJ provider abstractions remain static until runtime integration.

## 7. Core infrastructure
Configuration governance, permissions/capability checks, audit/provenance, task lifecycle, recovery, capability registry, logging, and memory interface contracts — all AJ-governed by design target.

## 8. Repository boundaries
Keep `AJ`, `JARVIS`, `HELIX`, `Hermes` (and supporting services like Honcho integration) **independently maintainable**. No convenience merges.

## ASCII view
```text
                    +----------------------+
                    |   AJ Control Plane   |  (target; code foundation exists)
                    | policy/orchestration |
                    | task/audit/cap/mem   |
                    +----------+-----------+
                               |
          +--------------------+--------------------+
          |                    |                    |
 +--------v-------+   +--------v-------+   +--------v--------+
 |    JARVIS      |   |     HELIX      |   |     Hermes      |
 | personal agent |   | execution/UI   |   | workflow/skills |
 | (separate)     |   | (separate)     |   | runtime (active)|
 +----------------+   +-------+--------+   +--------+--------+
                              |                     |
                        helix-live/globe      Honcho client/plugin
                       (active paths)         (writer unproven)
                                                  |
                                           +------v------+
                                           |   Honcho    |  candidate adapter/index
                                           | PG18 schema |  NOT canonical now
                                           +-------------+
```
