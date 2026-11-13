# Batch 05 Master Report — Identity, Writer Evidence & Port 8000 Resolution

**Project:** AJ / JARVIS / HELIX / Hermes / Honcho  
**Workspace:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`  
**Mode:** A1 read-only, A2 metadata-only Honcho counts (no sensitive contents), A4 preserved. Privileged **read-only** port 8000 inspection performed with elevation approval. **No unauthorized mutations.**

## Success criteria
| Criterion | Result |
|---|---|
| 1. Port 8000 owner identified OR exact technical blocker established | **Resolved (owner identified):** PID 973 `legacy-printer-app` (system, non-ecosystem), 0.0.0.0/::8000 |
| 2. Hermes→Honcho writer behavior proven/disproven/rigorously blocked | **Rigorously unresolved:** static write capability proven; runtime load/invocation/persistence unproven; A2 still 0 messages/conclusions; controlled delta test not performed (needs approval; DB writes) |
| 3. AJ/JARVIS/HELIX runtime identities mapped | **Mapped with key clarification:** AJ no runtime; JARVIS gateway inactive/missing path; HELIX live runtime = `AI_WORKSPACE/helix` (clean 99c7a38), home helix dirty e8a64cf not active runtime; globe separate |
| 4. JARVIS application-source uniqueness resolved as far as possible | **Resolved (filtered scope):** 259/259 source files common, 0 unique app source; only `startup.log` differs |
| 5. HELIX Build Spec mapping substantially complete | **Substantial/PARTIAL:** major features mapped to spec/runtime/impl state; intent/equivalence still unresolved |
| 6. Memory architecture candidates compared using evidence | **Completed** (Candidate A preferred as target direction, not implemented; confidence Medium) |
| 7. Network exposure matrix complete | **Completed** (8000–3200 matrix; unknowns marked `UNKNOWN — DO NOT ASSUME SAFE`) |
| 8. Implementation readiness reassessed | **Completed**: remains **NOT READY** |
| 9. All required reports exist | **Yes (13 reports + manifests)** |
| 10. No unauthorized mutation occurs | **Confirmed** |

## Resolved facts (new)
- Port 8000 is **`legacy-printer-app.service` / `/usr/sbin/legacy-printer-app server` (PID 973, root)**, exposed on all interfaces; **unrelated to AJ ecosystem**. Intent/auth UNVERIFIED.
- JARVIS backup “unique app source” concern is resolved in filtered analysis: no unique application source files; differences were runtime artifacts (venv/profile/chat history) plus `startup.log`.
- Active HELIX live proxy source is **`AI_WORKSPACE/helix`** (`99c7a38`, clean), not the dirty `/home/abubakargcx/helix` worktree.
- Hermes Honcho plugin contains concrete turn-sync/write code paths and config gates, but **no evidence of successful runtime message persistence** (Honcho still 0 messages/conclusions).

## Still blocked
- Hermes→Honcho runtime activation/invocation/persistence and writer attribution (needs approved controlled metadata-delta test and/or deeper Hermes core hook proof).
- Canonical AJ runtime/source and JARVIS activation/role decision.
- HELIX refactor intent and spec equivalence (`AI_WORKSPACE/helix` active path vs home dirty WIP/refactor tree).
- Exposure intent/auth for 8000/3389/5432/5434/8765.

## Architectural consequence
- **AJ:** control-plane foundation exists in code, not verified as running; must be explicitly activated/selected.
- **JARVIS:** legacy code preserved and source-equivalent across backups (filtered), but no active runtime/launcher; identity remains a decision, not an inference.
- **HELIX:** split state — active live proxy uses clean workspace repo; home repo is preserved dirty refactor/WIP. Treat as two states requiring reconciliation decision.
- **Hermes:** active execution runtime; Honcho integration is **capability-present, runtime-unproven**.
- **Honcho:** healthy capable PG18 backend; **not proven canonical memory** (0 messages/conclusions, unknown writer flow).

## Implementation status
**`NOT READY`**

## Next batch (safest)
**Batch 06 — Canonical Decisions & Controlled Writer Validation (decision-gated, minimal-risk):**
1. **User decisions (required):** AJ canonical runtime/source and role vs legacy JARVIS; HELIX canonical working tree/intent; exposure intent priorities.
2. **If explicitly approved:** isolated Hermes→Honcho **metadata-delta** test (synthetic, no personal content, no payload logging) + Hermes core plugin-load/hook trace.
3. **A1 read-only:** disposable-copy HELIX spec compliance/build-entrypoint validation (no service deployment, no original modification).
4. **Security follow-up (approved):** read-only config/auth review for exposed 8000/3389/5432/5434/8765; A3/GREEN SIGNAL for any changes.
