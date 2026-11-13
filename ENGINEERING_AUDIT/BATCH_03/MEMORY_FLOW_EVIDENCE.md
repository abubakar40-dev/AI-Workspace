# Memory Flow Evidence (Phase 7 synthesis)

## Verified facts (metadata/config/code; no row contents)
- **Honcho service:** running at `127.0.0.1:8123` (`honcho_local/honcho_server.py`, PID 893598) — VERIFIED (B306).
- **Honcho database backend:** PostgreSQL 18.6, local socket port 5433, DB `honcho` (8190 kB) — **VERIFIED (A2 metadata)**. Matches server code target.
- **Honcho schema (metadata):** tables `workspaces, sessions, peers, messages, conclusions, scopes, configuration`; extensions `vector, pg_trgm, plpgsql`; columns include `content`/`embedding`/metadata/timestamps — **VERIFIED structure, no content selected**. Aggregate activity minimal: 2 workspaces, 1 session, 0 messages/conclusions (2026-11-09 timestamps).
- **Hermes integration signals:** `~/.hermes/honcho.json` → `http://localhost:8123` local (key redacted); installed `~/.hermes/plugins/honcho` implementation package — **VERIFIED configured/capable**.

## Flow status (required paths, evidence-based)
| Flow | Status | Evidence | Gap |
|---|---|---|---|
| User conversation → Hermes → Honcho | **Configured/Possible; runtime writes UNVERIFIED** | Hermes Honcho config+plugin; Honcho healthy+PG18 backed | no hook/log trace proving Hermes wrote; Honcho aggregates don’t identify writer |
| User task → AJ → JARVIS/HELIX | **UNVERIFIED / foundation-only** | AJ foundation code exists; no active AJ runtime mapped | runtime wiring unknown |
| JARVIS/HELIX task result → AJ | **UNVERIFIED** | — | — |
| AJ memory retrieval → agent context | **UNVERIFIED** | AJ has `memory.py`; no runtime evidence | — |
| Raw event → summary/derived memory | **UNVERIFIED** | Honcho has `conclusions`/embeddings schema; 0 rows observed | actual processing/writer unknown |
| Backup → recovery path | **UNVERIFIED** | no verified backup/restore for Honcho PG18 `honcho` DB or Hermes state | — |

## Writer identification discipline
- **A configuration reference ≠ verified writer.** Hermes is configured to reach Honcho; DB metadata alone does not prove Hermes created existing workspaces/session.
- Honcho DB currently shows **no messages/conclusions** (aggregate), limiting historical-write evidence.

## Canonical memory (AJ)
**No functioning canonical AJ memory implementation verified in runtime.** `AI_WORKSPACE/AJ` contains memory-related code but no mapped active process/service using it as the ecosystem canonical store. Hermes maintains local state under `~/.hermes` (operational); Honcho is a capable/configured memory-related service but not proven canonical or actively populated with conversation messages in current aggregates.
