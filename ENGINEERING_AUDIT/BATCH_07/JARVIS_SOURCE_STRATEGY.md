# JARVIS Future Source Strategy

**Mode:** read-only. No JARVIS repository, backup, branch, or service was modified. Related work: `BATCH_07_DECISION_RATIFICATION.md` (E5–E8, R3–R4), `BATCH_07_IMPLEMENTATION_GATE.md`.

---

## 0. Corrected baseline (this is new, and it changes the question)

Batch 05 concluded that JARVIS existed only as two preserved backups plus a dead service pointing at a missing `/home/abubakargcx/JARVIS`. **Batch 07 disproves the "backups only" part:**

| Property | `AI_WORKSPACE/JARVIS` (live source) | `backup/JARVIS-old-repo-20261106` | `backup/JARVIS-nested-duplicate-20261106` |
|---|---|---|---|
| Exists | **Yes** | Yes | Yes |
| Git repo | **Yes**, HEAD `d93c702`, branch `audit/consolidation-2026-11-06`, no remote | Yes (snapshot) | Yes (snapshot) |
| Position | **3 commits ahead of `master` (`cffa32d`)** | historic | historic |
| Size | 1.9 GB (venv 1.6 GB, config 168 MB) | — | — |
| Filtered source files | 197 | 223 (nested) | 223 |
| Distinctive content | `core/policy.py`, `core/audit.py`, `core/capabilities.py`, `core/confirmation.py`, `config/__init__.py` | Brahma/smart-home gateway code | Brahma/smart-home gateway code |
| Active runtime | **No** (gateway unit inactive, wrong path) | No | No |

So JARVIS is **not** a lost project awaiting restoration. It is a *consolidated, committed, non-running* application whose newest work — policy, audit, confirmation, capability core, and the deliberate removal of smart-home code — exists **only** in `AI_WORKSPACE/JARVIS`.

That reframing matters: Option A and Option B below were previously "backup vs rewrite." Now they are "continue the consolidated tree" vs "spec-first reimplementation."

---

## Option A — Continue from the existing preserved JARVIS source

Interpreted narrowly as: use `AI_WORKSPACE/JARVIS` (audit branch) as the JARVIS development baseline.

| Dimension | Assessment |
|---|---|
| **Advantages** | Zero loss of the consolidation work (`core/policy.py`, `core/audit.py`, `core/confirmation.py`, `core/capabilities.py`). 106 Python files of real, runnable behaviour: `agent_runtime.py`, `bridge_ws.py`, `command_center.py`, `desktop_input.py`, `gui/`, plus a `tests/` suite (`test_core_policy.py`, `test_computer_control_wiring.py`, `test_command_interactions.py`…). Immediately demonstrable capability, which matters for a personal assistant. History and commit intent are intact and legible. |
| **Risks** | Inheritance of Windows-first assumptions (PyQt desktop, audio devices) in a Linux-rooted ecosystem. 1.6 GB venv is environment-coupled and will not travel. Upstream licence/branding (`TRADEMARK.md`, upstream README) is bound to the original project, complicating later distribution. The audit branch is unmerged, so `master` is *behind* it — a canonical-tree decision (U3) is a prerequisite. |
| **Preservation implications** | Nothing needs restoring; both backups stay untouched. The live tree is already the newest state, so preservation risk is *low* — the opposite of the B05 assumption. |
| **Architectural implications** | JARVIS keeps its own runtime loop and becomes an `AgentRequest`/`AgentResult` peer to AJ. Its existing `core/policy.py` + `core/audit.py` will **overlap** AJ's `permissions.py` + `audit.py`, creating two policy engines. Resolving that overlap (JARVIS delegates policy to AJ, or JARVIS keeps a local cache) is real design work. |
| **Maintenance implications** | Moderate–high: one large desktop application, mixed Python/GUI concerns, heavy dependency surface. |
| **Relationship to AJ** | Clean *if* JARVIS is treated as a replaceable agent behind a contract. The risk is drift: JARVIS grows features AJ thinks it should own. |

---

## Option B — Clean JARVIS implementation contract, selectively reuse historical source

Write the JARVIS boundary first (agent identity, request/result shapes, capability declarations, memory-write obligations, policy delegation to AJ), then port only what satisfies the contract.

| Dimension | Assessment |
|---|---|
| **Advantages** | Avoids inheriting the dual-policy-engine problem by construction. Keeps JARVIS aligned to AJ contracts from day one. Lets the desktop/GUI layer be replaced incrementally instead of fought. Small executable surface. |
| **Risks** | Loses 106 files of working behaviour and its test suite unless ported deliberately — high effort, high chance of quietly dropping capability. Re-implements solved problems (`desktop_input.py`, `echo_guard`, `audio_device_resolution`). Delays any demonstrable personal-assistant capability. |
| **Preservation implications** | None required; backups and live tree remain the reference. |
| **Architectural implications** | Cleanest possible separation. JARVIS becomes a thin agent + adapters, with its heavy desktop concerns quarantined behind ports. |
| **Maintenance implications** | Low long-term, high short-term. |
| **Relationship to AJ** | Ideal: contract-first, AJ-governed policy, no duplication. |

---

## Option C — Hybrid: contract-first, live tree as the reference implementation

**Definition:** ratify `AI_WORKSPACE/JARVIS` as the canonical *source of truth and behaviour reference*, but do not extend it as a monolith. Write the JARVIS agent contract per Option B, and port capability into it **module by module**, deleting nothing from the tree until the ported path has parity.

| Dimension | Assessment |
|---|---|
| **Advantages** | Preserves all consolidation work while preventing the dual-policy-engine drift. Establishes the contract that AJ needs *now* without waiting for a rewrite. Gives a testable migration path: each ported module keeps its existing test as the parity gate. Nothing is thrown away to prove a point. |
| **Risks** | Two artefacts coexist during migration (contract module + legacy tree), which needs a stated end-state or it becomes permanent. Requires discipline to actually delete legacy paths once parity lands. |
| **Preservation implications** | Strongest: the legacy tree is retained *as evidence* until parity, then retired by decision (A3), not by accident. |
| **Architectural implications** | JARVIS ends as a contract-conforming agent (`AgentRequest` in, `AgentResult` out, policy delegated to AJ, memory writes recorded as canonical raw events) that still contains its hard-won desktop/audio logic behind ports. |
| **Maintenance implications** | Medium during migration, low after. |
| **Relationship to AJ** | Best fit: contract now, parity-gated porting, no duplication of policy or audit. |

---

## Recommendation

**Option C — `RECOMMENDED`.** Option A alone risks two competing policy/audit engines in one ecosystem; Option B alone discards 106 files of working, tested behaviour and both an audio and desktop-control stack that are expensive to rebuild. Option C takes the contract discipline of B and the substance of A, with the live tree as reference until per-module parity exists.

Concretely, the ordering is:

1. **Ratify the canonical tree (U3):** `AI_WORKSPACE/JARVIS`, audit branch, is the source of truth. Do not move `master` yet.
2. **Do not activate the gateway unit** — it targets a nonexistent path; retargeting is A3.
3. **Write the JARVIS agent contract** as part of the foundation plan (`BATCH_07_LIMITED_FOUNDATION_PLAN.md`, interface 9) — specification only.
4. **Port per module behind parity tests**, starting with policy/audit *delegation* (so JARVIS stops owning policy decisions) and leaving GUI/audio untouched.
5. **Retire legacy paths only after parity**, by explicit A3 decision.

**Confidence:** High on the evidence (tree contents, commit range, filtered diff, unit config). Medium on the migration estimate — no JARVIS test suite has been executed in any audit batch, so effort is unmeasured.

---

## Explicitly not endorsed

- Merging JARVIS into AJ, or AJ into JARVIS.
- Restoring Brahma/smart-home code (removed deliberately in `6ba652b`).
- Deleting or overwriting either backup.
- Copying `venv/` (1.6 GB) or `config/` (168 MB) anywhere — environment and local state, not source.
- Reviving `ExecStart=/home/abubakargcx/JARVIS/scripts/start-claude-gateway.sh`; that path does not exist.
