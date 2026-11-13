# Memory & Honcho Architecture Audit (Batch 01, partial)

## Honcho runtime (VERIFIED/OBSERVED)
- Honcho health: `GET http://localhost:8123/health` → `{"status":"ok","service":"honcho-server","database":"connected"}`.
- Process: `python -u honcho_server.py` (PID 893598) launched from `AI_WORKSPACE/honcho_local` with `~/.hermes/venv-honcho` (OBSERVED). Files present include `honcho_server.py`, `minimal_server.py`, `docker-compose.yml.example`, Hermes plugin dirs (`hermes-plugin-honcho`), Honcho CLI dirs.
- Hermes references Honcho via `~/.hermes/honcho.json` (base URL localhost:8123, local env; API key redacted). Hermes previously had Honcho command/plugin configured (context).

## Canonical memory (UNVERIFIED — critical)
Master doc requires AJ ecosystem-level canonical memory, provider-independent, raw records preserved, summaries traceable, backups/recovery tested. **This pass did not verify:**
- Where raw conversations/events/tasks are stored (Honcho DB, Hermes sessions, JARVIS/HELIX stores, Obsidian files, SQLite/JSON logs).
- Which Postgres/SQLite instance backs Honcho “database connected”.
- Hermes session persistence format and whether it duplicates Honcho/JARVIS memory.
- JARVIS/HELIX memory ownership, schemas, provenance, deduplication, conflict handling.
- Obsidian vault as navigation layer only vs accidental source-of-truth drift.
- Backup/restore tests (3-2-1).

## Provider independence (PARTIAL)
- Hermes default chat provider is now OpenRouter (verified), while Honcho remains separate service — positive separation of inference vs memory service. But actual memory ownership boundaries across Hermes/Honcho/JARVIS/HELIX remain **UNVERIFIED**.

## Recommendations (REQUIRES USER APPROVAL for changes; read-only investigation safe)
1. **Read-only map:** identify Honcho DB URL/config, tables/schemas (metadata only), Hermes session dirs/DBs, JARVIS/HELIX memory stores, Obsidian vault path and sync direction.
2. Define canonical record classes: raw conversation/event/task, structured memory, summaries/indexes, skill/workflow records — with provenance and immutable raw-log policy.
3. Add backup/restore validation plan before any migration or cleanup.
