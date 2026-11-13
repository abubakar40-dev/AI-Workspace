# Hermes → Honcho Writer Proof (Workstream B)

**Method:** A1 static/runtime metadata evidence; A2 metadata-only Honcho counts recheck. **No message contents read. No controlled DB-write test performed** (see B3). No config/service/DB mutations.

## B1. Static write-path trace (STATIC EVIDENCE)
`Hermes conversation/session` (caller hooks in Hermes runtime — **not fully traced into Hermes core in Batch 05**) → `~/.hermes/plugins/honcho/__init__.py` `HonchoMemoryProvider.sync_turn()` / initialization hooks → session/manager (`session.py`, `session_context.py`, peers/client modules) → Honcho client/API calls → `honcho_local/honcho_server.py` HTTP endpoints (`/v3/.../sessions/{id}/messages/`, sessions, conclusions, etc.) → PostgreSQL 18 DB `honcho` (port 5433).

**Key static findings (file:line evidence from inspection):**
- `__init__.py`: plugin class/config/`initialize(session_id,...)`, lazy/eager init (`init_on_session_start`), `_writes_enabled()` checks `save_messages` and cron/flush context, `sync_turn()` sanitizes content, skips internal gateway/empty turns, enforces bot/a2a session routing, resolves author peer, chunks messages (`_chunk_message`, `message_max_chars`), calls `session.add_message(...)` for user/assistant chunks, then `self._manager.save(session)` (honors write frequency), runs via background thread `_spawn_write` (failures logged, not raised). `on_turn_start`/prefetch/session switch hooks exist.
- `session.py`: local message cache; async writer/flush/save mechanisms present (`_flush_session`, `save`, async queue/thread start/stop semantics observed in grep); `add_message` appends timestamped messages.
- `client.py`/config: host/config resolution, `save_messages`/`write_frequency`/`init_on_session_start`/observation/dialectic/query-rewrite options; per-identity config paths.
- `honcho_server.py`: POST/GET message/session/conclusion endpoints exist (API surface for writes/reads).

**Error/retry/disable conditions (partial):** `save_messages` false, cron/flush/internal gateway turns, empty turns, bot/a2a rules, init not ready (may kick init), async write failures logged. Full retry/flush-failure semantics **not exhaustively audited**.

## B2. Runtime activation evidence
| State | Evidence | Assessment |
|---|---|---|
| Configured | `~/.hermes/honcho.json` has base URL `http://localhost:8123`, env local, key redacted | **VERIFIED** |
| Installed | plugin present under `~/.hermes/plugins/honcho/*`; Hermes CLI/profile references | **VERIFIED** |
| Loaded | runtime load not observed in logs during Batch 05 | **UNVERIFIED** |
| Invoked | no direct runtime hook invocation proof | **UNVERIFIED** |
| Successfully persisted (messages/conclusions) | A2 metadata-only recheck (2026-11-10): `workspaces=2, sessions=1, peers=0, messages=0, conclusions=0` (no content read) | **NOT OBSERVED / no verified message writes** |

Honcho service is healthy (Batch 03). DB metadata alone cannot attribute existing session/workspace creation to Hermes.

## B3. Controlled isolated metadata-delta test
**NOT PERFORMED.** Reason: creating/sending even a synthetic interaction through Hermes-to-Honcho write paths would create database records/test traffic and may alter DB state; Batch 05 authorization prohibits database writes. Performing it requires explicit approval (scope-limited controlled test) and a safe isolation plan. No pre/post message-delta test executed.

## Conclusions
- **Hermes is a Honcho writer by implementation capability (static):** plugin contains real message/session persistence logic and Honcho server exposes write endpoints. **Confidence: High (static capability).**
- **Hermes is NOT proven as an active runtime Honcho writer:** runtime activation/invocation/persistence not verified; current Honcho message/conclusion counts are 0. **Confidence: Medium that active message writes are not occurring in observed state; Low for “plugin never loaded/invoked”.**
- **Honcho as canonical memory store (current state):** backend/schema healthy and capable, but **cannot be considered verified canonical ecosystem memory store** yet due to unproven writer flow, provenance, and zero observed message/conclusion writes. **UNVERIFIED for canonical operational status.**
