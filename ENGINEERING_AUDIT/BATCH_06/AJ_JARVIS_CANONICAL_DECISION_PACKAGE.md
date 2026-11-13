# AJ / JARVIS Canonical Decision Package (Workstream B)

**Status labels used:** `EVIDENCE-ESTABLISHED`, `RECOMMENDED`, `USER DECISION REQUIRED`, `DEFERRED`. No repos modified.

## B1. AJ assessment (`AI_WORKSPACE/AJ`)
| Area | Evidence | Assessment |
|---|---|---|
| Architecture/foundation | ports/adapters-style modules: `orchestrator, task, memory, permissions, capability, providers, router, config, audit, agents, skills, interfaces` | **EVIDENCE-ESTABLISHED**: strongest control-plane foundation in repo evidence |
| Memory foundation | SQLite `raw_events` append-only intent, summaries cite raw IDs, basic substring retrieval, provider-independent provenance label (static) | **EVIDENCE-ESTABLISHED** (static design/impl); runtime UNVERIFIED |
| Task lifecycle | `task.py` JSONL persistence, transitions/events concepts | **EVIDENCE-ESTABLISHED** (static) |
| Provider abstraction | `providers` module present; Hermes separately verified on OpenRouter default | **PARTIAL** (AJ runtime wiring unverified) |
| Permissions/audit/capability | modules present | **STATIC/UNVERIFIED runtime** |
| Tests | 6 suites: `test_foundation.py`, `test_memory.py`, `test_orchestrator.py`, `test_providers.py`, `test_calling.py`, `test_hermes_contract.py`, plus `conftest.py` | **PRESENT, NOT RUNNABLE as-is** (see B1a) |
| Runtime readiness | no mapped active process/entrypoint/service in B03–B05 scans; **no entrypoint module** (`main.py`/`__main__.py`/`cli.py` absent) | **EVIDENCE-ESTABLISHED**: not runtime-active, no launch surface |

### B1a. Runnability check (new, VERIFIED)
| Check | Result |
|---|---|
| Packaging/dependency declaration | **None found** — no `pyproject.toml`, `requirements*.txt`, `setup.cfg`, `pytest.ini` at repo root |
| Virtualenv | **None** in `AJ/` (`.venv`, `venv` absent) |
| Test execution | `python3 -m pytest tests -q` → **`No module named pytest`** (system Python 3.14.4). Tests were **not** executed; installing pytest is an environment change outside this batch |
| Consequence | AJ cannot currently be installed, tested or launched from a clean environment without decisions about packaging, dependency pinning and entrypoint — a concrete, bounded first implementation task |

Module inventory present: `agents, audit, calling, capability, config, contracts, errors, execution, ids, integrations, memory, orchestrator, permissions, providers, task`. This is broader than the B05 summary (notably `calling`, `contracts`, `execution`, `integrations`), strengthening the control-plane assessment.

## B2. JARVIS assessment (legacy backups)
| Area | Evidence | Assessment |
|---|---|---|
| Application capabilities | legacy assistant app structure (`Jarvis/`, `core/`, `api/`, `tools/`, `memory/`, `ui/`, configs/scripts) | **EVIDENCE-ESTABLISHED** historical codebase exists |
| Source completeness (filtered) | B05: 259/259 common app-source files, 0 unique source files between backups; 1 log diff | **EVIDENCE-ESTABLISHED** backups are source-equivalent in filtered scope |
| Runtime architecture | `jarvis-claude-gateway.service` inactive, points to missing `/home/abubakargcx/JARVIS` | **EVIDENCE-ESTABLISHED** no active mapped runtime |
| Historical/integration value | preserved snapshots, prior JARVIS features/context; integration path to AJ unclear | **RECOMMENDED** preserve as historical/reference material; do not assume active canonical |

## B3. Target model evaluation (AJ/JARVIS/HELIX/Hermes separation)
| Role | Fit with evidence | Label |
|---|---|---|
| AJ = control plane/governance/orchestration | fits AJ foundation modules and master context; no runtime mapped yet | **RECOMMENDED** |
| JARVIS = personal-facing assistant agent | fits identity intent; legacy code exists but no active runtime; keep separate identity | **RECOMMENDED / USER DECISION REQUIRED** (scope + source) |
| HELIX = advanced execution agent | active live proxy/runtime split exists; separate project identity | **RECOMMENDED** |
| Hermes = reusable workflow/skill execution runtime | active gateway/runtime; Honcho memory writes unproven | **EVIDENCE-ESTABLISHED** as runtime; **RECOMMENDED** keep non-canonical for memory |

## B4. Decision matrix
| Decision | Option A | Option B | Evidence | Recommendation | Risk | Status |
|---|---|---|---|---|---|---|
| AJ canonical control plane | `AI_WORKSPACE/AJ` foundation becomes canonical control-plane source (after explicit activation plan) | Keep AJ as dormant/reference only | AJ has orchestration/task/memory/audit/provider foundations; no runtime mapped | **Option A** as development target, subject to runtime entrypoint/activation plan | activating wrong assumptions; missing runtime wiring | **RECOMMENDED / USER DECISION REQUIRED** |
| JARVIS role | Independent personal assistant agent (future runtime) fed by contracts from AJ | Fold into AJ/HELIX | master context separation; backups source-equivalent but inactive; missing active path | **Independent agent role**; preserve backups; do not merge now | duplicate effort, unclear migration | **RECOMMENDED** |
| Legacy JARVIS backups | Preserve both read-only; use source-equivalent filtered result as reference | Delete/dedupe/merge | B05 shows no unique app source (filtered); runtime artifacts differ; no active runtime | **Preserve both; no deletion/merge** | accidental loss if deleted | **EVIDENCE-ESTABLISHED safe action = preserve**; canonical use **USER DECISION REQUIRED** |
| AJ/JARVIS repo relationship | Separate repos/identities with explicit contracts | Merge for convenience | current evidence supports modular separation; no proof merge needed | **Keep separate** | coupling/identity loss | **RECOMMENDED** |
| Runtime entrypoint | Define/implement AJ runtime entrypoint later (approved plan) from `AI_WORKSPACE/AJ` | Use legacy JARVIS launcher paths | AJ no entrypoint mapped; JARVIS gateway inactive/missing `/home/abubakargcx/JARVIS` | **New/explicit AJ entrypoint in approved implementation phase**; do not revive stale missing-path launcher | premature activation | **RECOMMENDED / DEFERRED to implementation gate** |
