# Memory Architecture Comparison (Workstream F)

**Scope:** evidence-based comparison only. No decision implemented.

## Candidates
- **A:** AJ local raw-first memory as canonical, with Honcho as adapter/index/derived service.
- **B:** Honcho as canonical memory backend, with AJ acting as governing memory adapter.

## Evaluation
| Criterion | Candidate A: AJ raw-first canonical + Honcho adapter/index | Candidate B: Honcho canonical backend + AJ adapter/governor | Evidence |
|---|---|---|---|
| Provider independence | Strong if AJ store is local/provider-neutral (AJ `memory.py` has no model-provider coupling intent) | Depends on Honcho API/schema/ops; backend replaceability must be abstracted | AJ memory static (D405/B04); Honcho PG18/HTTP API (B03) |
| Raw event preservation | Native fit (AJ `raw_events` append-only intent, summaries cite raw IDs) | Possible if Honcho preserves raw messages/events with provenance; not verified as used | AJ static; Honcho schema has messages but 0 rows/no writer proof |
| Conversation continuity | Requires AJ runtime + ingestion adapters from Hermes/JARVIS/HELIX | Natural if writers persist; currently no verified Hermes writes | B05 writer proof: 0 messages |
| Task/event history | AJ `task.py` JSONL + memory design fits orchestration | Honcho is conversation/memory-centric; task semantics may need extension/mapping | AJ static; Honcho schema |
| Provenance | AJ fields/model label/provenance intent; must be enforced | Must verify Honcho stores/writes provenance per source/writer | static vs unverified runtime |
| Search/retrieval | AJ currently basic substring (static); indexes rebuildable | Honcho/PG/vector extensions present; retrieval not verified end-to-end | AJ static; Honcho extensions `vector,pg_trgm` |
| Summarization | AJ summaries cite raw IDs (design) | Honcho has conclusions; runtime generation/writer unverified | AJ static; Honcho 0 conclusions |
| Recovery/backups | Local files/SQLite easier to snapshot if paths known; AJ runtime unverified | Requires PG backup/restore discipline; single DB backend | HELIX backup pattern proven; Honcho backup not verified |
| Restore | Simple if canonical is files; adapters rebuildable | DB restore affects all writers; needs tested procedures | UNVERIFIED for both ecosystems |
| Multi-agent access | Needs AJ service/contract; single-file SQLite can contend | Central HTTP/DB service fits multi-agent access if governed | Hermes/Honcho service architecture vs AJ unmapped |
| Future model/provider replacement | Strong (raw-first local canonical) | Strong only if AJ governs contracts and storage abstraction remains | master context principle |
| Long-term scalability | SQLite/local limits; may need evolution | PG18 backend already present; operational complexity higher | current infra |
| Existing implementation | AJ memory/task code exists (static) but no runtime | Honcho backend running with schema; Hermes plugin can write (static) but not proven | B03/B04/B05 |
| Runtime evidence | AJ unmapped | Honcho service healthy; **no verified writers/message persistence** | B305, A2/B05 counts |
| Data ownership clarity | Clear if AJ is canonical owner by contract | Currently unclear (writer identity unproven) | writer proof unresolved |
| Failure isolation | AJ local can isolate agent memory; adapters fail independently | Honcho outage affects shared memory path | Hermes must handle Honcho unavailable (unverified) |

## Recommendation (NOT implemented)
**Prefer Candidate A as the target direction (AJ-governed raw-first canonical memory), treating Honcho as a candidate adapter/index/derived-memory service — but only after writer/contract validation.** 
- **Evidence:** AJ already encodes the master-context principles (raw events, summaries citing raw IDs, provider-independent provenance label, append-oriented intent). Honcho is operationally present but has 0 messages/conclusions and no verified Hermes writer, so making it canonical now would create a false source-of-truth.
- **Advantages (A):** aligns with raw-first/provenance/rebuildable-index principles; reduces split-brain risk; keeps AJ as CEO/control-plane owner.
- **Risks (A):** AJ runtime is unverified; requires adapter wiring and migration design.
- **Advantages (B):** existing PG/service/schema/vector capability; multi-client access.
- **Risks (B):** unproven writer semantics/provenance/ownership; central dependency; could repeat hidden writer problem.
- **Migration complexity:** Medium-High either way (needs contracts, provenance, backfill decisions).
- **Recovery implications:** whichever becomes canonical needs verified backup/restore; raw-first canonical should be independently recoverable.
- **Confidence:** **Medium** (constrained by unresolved writer/runtime identity).
