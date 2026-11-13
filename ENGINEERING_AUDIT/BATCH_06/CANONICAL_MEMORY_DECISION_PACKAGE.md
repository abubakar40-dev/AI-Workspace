# Canonical Memory Decision Package (Workstream E)

**Decision labels:** `EVIDENCE-ESTABLISHED`, `RECOMMENDED`, `USER DECISION REQUIRED`. No implementation.

## Inputs (B01–B06)
- Honcho PG18 backend healthy, schema capable; A2 metadata still `2 workspaces/1 session/0 peers/0 messages/0 conclusions` (no content). *(EVIDENCE-ESTABLISHED)*
- Hermes Honcho plugin: static write capability present (`sync_turn`/save path) but runtime writer **not verified**; B06 observed synthetic turn misrouted to Honcho as LLM provider (404), test inconclusive. *(PARTIALLY VERIFIED / TEST INCONCLUSIVE)*
- AJ `memory.py`/`task.py`: raw-first/append-oriented intent, summaries cite raw IDs, basic retrieval, provenance label, provider-independent design (static); no active AJ runtime mapped. *(EVIDENCE-ESTABLISHED static)*
- Master context requires provider-independent canonical memory; Hermes not CEO/canonical owner.

## Option comparison
| Criterion | Option A — AJ raw-first canonical (Honcho adapter/index/derived) | Option B — Honcho canonical backend (AJ governs/adapts) |
|---|---|---|
| Raw-data preservation/provenance | Strong native fit (AJ raw events + cited summaries) | Possible, but not proven in current runtime/writer semantics |
| Provider independence | Strong | Conditional on abstraction; backend-coupled risk |
| Actual runtime evidence | AJ runtime unmapped | Honcho service healthy but **no verified writers/message persistence** |
| Writer proof | N/A to AJ runtime today (gap) | **Missing** for Hermes/Honcho path; cannot claim canonical operation |
| Multi-agent access/retrieval | needs service/contract layer | central API/PG advantage |
| Recovery/backup | simple if file-based canonical; unverified ops | PG backup discipline needed; unverified |
| Failure isolation | better if AJ-owned adapters degrade gracefully | shared backend dependency |
| Migration complexity | Medium-High | Medium-High |

## Recommendation (explicit)
- **Canonical owner (target):** **AJ** (control plane) — **RECOMMENDED / USER DECISION REQUIRED**.
- **Raw-data owner (target):** **AJ-governed raw-first append-oriented store** (conversations/tasks/events with provenance/timestamps) — **RECOMMENDED**.
- **Derived/index owner (target):** rebuildable layers (search/vector/summaries) — may use **Honcho and/or AJ-managed indexes** as adapters, not silent canonical owners — **RECOMMENDED / DEFERRED detail**.
- **Summary owner:** derived summaries must cite/provenance-link raw records; generation/writer governed by AJ contracts — **RECOMMENDED**.
- **Retrieval interface owner:** AJ-defined interface/adapters; implementations replaceable — **RECOMMENDED**.
- **Backup responsibility:** canonical raw store + config/metadata backups; Honcho PG backups if/when used as adapter/index — **RECOMMENDED**.
- **Migration requirement:** **DEFERRED** pending AJ runtime decision and verified writer/adapter contracts. If synthetic Honcho records exist from future tests, handle by explicit approved plan (no ad hoc destructive cleanup).
- **Confidence:** **Medium** (upgraded rationale: write gates are confirmed on by default — `saveMessages=true`, `writeFrequency=async`, hook `on_session_end` — so the 0-message state is explained by “no completed turn,” not by a disabled writer. That weakens, but does not remove, the case for Honcho-as-canonical).

## Why not Option B today (explicit)
Option B requires Honcho to already be the authoritative store. Evidence shows the opposite: the only runtime integration is unexercised (0 messages), its writes are lifecycle-driven and asynchronous, there is no verified writer attribution, and the ecosystem’s own raw-first design exists in AJ. Adopting Option B now would make an unproven, provider-coupled path canonical by decree — exactly what the governing context forbids.

## Critical rule
**Do not treat Honcho as canonical memory** while Hermes writer proof remains `TEST INCONCLUSIVE` and message/conclusion persistence is unobserved/unattributed. *(EVIDENCE-ESTABLISHED constraint)*
