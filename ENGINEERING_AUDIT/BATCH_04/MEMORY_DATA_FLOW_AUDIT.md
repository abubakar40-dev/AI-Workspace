# Memory Data-Flow Audit (Workstream A)

## A1. Hermes → Honcho
**Static/config evidence (VERIFIED):**
- Hermes config: `~/.hermes/honcho.json` → `HONCHO_BASE_URL=http://localhost:8123`, local env, API key present (**redacted**). Honcho server healthy (8123) backed by PG18 `honcho` DB (A2, Batch 03).
- Hermes Honcho plugin installed: `~/.hermes/plugins/honcho/` (`__init__`, `client.py`, `cli.py`, `session*.py`, `dialectic.py`, `setup.py`, etc.). `__init__` shows `initialize(session_id, ...)`, session key resolution, lazy/eager init (`init_on_session_start`), tools-only deferred init, background session init (`_start_session_init_background`), config/session-start component handling.
- Hermes CLI references Honcho profile/setup/migration and `import_provider_module("honcho","cli")` during profile operations (D406).

**Questions:**
| Question | Finding | Confidence |
|---|---|---|
| Plugin actually loaded during Hermes startup? | Plugin package/config integration exists; runtime load/activation not traced from logs | **UNVERIFIED** |
| Hermes invokes Honcho automatically? | Lifecycle hooks/init paths exist in plugin code; automatic invocation in current runtime **UNVERIFIED** | UNVERIFIED |
| Which lifecycle events trigger writes? | Static code suggests session init/turn/tool/message-related handling; exact write triggers **not fully traced** in this batch | UNVERIFIED (static hints) |
| Conversations/messages/summaries/conclusions persisted? | Honcho schema supports messages/conclusions; A2 aggregates show **0 messages, 0 conclusions, 1 session, 2 workspaces** | VERIFIED schema/counts; **no verified Hermes message writes** |
| Writes sync/async? | background init/thread hints in code; write-path sync/async not fully proven | UNVERIFIED |
| Behavior if Honcho unavailable? | error handling not fully audited | UNVERIFIED |
| Retries? | not fully audited | UNVERIFIED |
| Duplicate writes possible? | not audited | UNVERIFIED |
| Session/identity mapping? | session key resolution exists; actual IDs/provenance in DB not attributed to Hermes | UNVERIFIED |
| Logs/safe metadata prove real writes? | A2 aggregates insufficient to attribute writer; no message contents inspected | **NOT VERIFIED** |

## A2. AJ memory implementation (static, D405)
| Aspect | Evidence | Assessment |
|---|---|---|
| Storage backend | `AJ/aj/memory.py`: `sqlite3.connect(...)`, `raw_events` table, summaries table concepts; `aj/task.py`: JSONL task persistence | **Implemented in code (SQLite + JSONL patterns)** |
| Persistence | file-backed SQLite/JSONL | **Designed/implemented**; runtime use UNVERIFIED |
| Survives restarts | file-backed store | **Likely if used**; UNVERIFIED runtime |
| Provider-independent | local storage, no model-provider coupling in memory layer; `model` on summary is provenance label only (comment) | **Design intent present**; VERIFIED in code intent |
| Raw vs summaries separated | `raw_events` append-only intent; summaries must cite raw event IDs; `verify()` concept | **Implemented conceptually**; tests/runtime UNVERIFIED |
| Provenance preserved | source/task_id/meta fields; model label noted | **Partial/implemented fields** |
| Retrieval implemented? | “plain substring search over both layers; no embeddings” (comment/grep) | **Basic retrieval in code (static)**; quality/runtime UNVERIFIED |
| Tests proving implementation | not executed in this batch | UNVERIFIED |

**Distinction:** AJ memory is **working/scaffold code present in repo** (not mere docs), but **runtime-verified canonical operation is UNVERIFIED** (no mapped active AJ process).

## A3. JARVIS and HELIX memory (limited static/runtime evidence)
- **JARVIS backups:** contain `memory/` dirs and broader legacy app structure (Batch 02/03). Detailed memory mechanisms (embeddings/vector stores/summarization/retrieval/session continuity) **not fully inventoried** in Batch 04 due scope; private contents not inspected.
- **HELIX:** memory implementation not fully mapped; helix-live runs separately and references `JARVIS_ROOT` env. UNVERIFIED.
- **Hermes local state:** `~/.hermes/state*.db`, sessions/request dumps — operational state (OBSERVED), not proven canonical ecosystem memory.

## A4. Memory ownership matrix
| Component | Storage | Writes data? | Reads data? | Persistent? | Runtime verified? | Evidence |
|---|---|---|---|---|---|---|
| Hermes (local) | SQLite/files under `~/.hermes` (state/sessions) | OBSERVED capability | OBSERVED | Yes (files) | process running; semantics partial | B306, B305 |
| Hermes → Honcho client | via API to Honcho 8123 | **UNVERIFIED actual** | **UNVERIFIED actual** | N/A | no | D406, D407 |
| Honcho server/DB | PG18 `honcho` DB port 5433 (schema verified) | API-capable; some records exist | API-capable | Yes | service/DB verified; **writer identity unverified** | D407 |
| AJ foundation (`aj/memory.py`) | SQLite/JSONL design in code | code supports | code supports | if used | **no active runtime mapped** | D405 |
| JARVIS legacy backups | legacy `memory/`/app stores (unknown detail) | unknown | unknown | unknown | no active runtime mapped | D408/Batch 02 |
| HELIX | unknown | unknown | unknown | unknown | partial services only | D409 |

## Proposed provider-independent canonical memory ownership model (RECOMMENDATION — NOT IMPLEMENTED)
- **Canonical owner (target): AJ control plane** for ecosystem-level raw conversation/task/event records, with append-only/raw-first semantics and provenance/timestamps.
- **Hermes:** execution runtime; may emit events/artifacts but should not become silent canonical owner without AJ-governed contract.
- **Honcho:** candidate memory service/adapter **subject to validation** (schema capable; writer/flow/provenance/retention not yet proven). Use only through explicit, auditable integration.
- **JARVIS/HELIX:** project-local working memory allowed; canonical cross-agent facts/events should flow through AJ-governed contracts.
- **Layers:** immutable/append-only raw history; derived summaries linked to raw IDs; rebuildable search/vector indexes; backup/restore; provider/model independence. *This is a proposed design direction, not approved/implemented architecture.*
