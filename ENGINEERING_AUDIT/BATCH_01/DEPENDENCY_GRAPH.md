# Dependency Graph (Batch 01, partial text)

```text
User (AbuBakar)
  └─ AJ (logical CEO/control plane; target) — implementation state UNVERIFIED
       ├─ JARVIS (sub-agent/project) — canonical active path UNVERIFIED (/home/JARVIS missing; AJ foundation + backups exist)
       ├─ HELIX (sub-agent/project) — /home/abubakargcx/helix (dirty git)
       └─ Hermes (runtime/skills) — ~/.hermes, v0.23.0, gateway+WhatsApp bridge running
            ├─ Provider: OpenRouter openrouter/auto (VERIFIED baseline)
            ├─ Honcho integration config (~/.hermes/honcho.json, redacted key)
            └─ OmniRush: Hermes integration removed; proxy healthy/preserved (separate)

Honcho server (localhost:8123, healthy, DB connected)
  ├─ Code: AI_WORKSPACE/honcho_local (git dirty/untracked local servers)
  ├─ Venv: ~/.hermes/venv-honcho (OBSERVED)
  └─ Actual DB backend: UNVERIFIED (could be Postgres 18/main 5433, docker DBs 5432/5434, SQLite, or other — map required)

PostgreSQL/Docker (OBSERVED, ownership UNVERIFIED)
  ├─ docker postgres:17 thedentallounge-db-1 :5432
  ├─ docker postgres:17 dental-lounge-ui-v2-db-1 :5434
  └─ system postgres 18/main + local 5433 listeners

AI_WORKSPACE (mounted, active source for Honcho; contains AJ foundation, backups, planning docs)
```

Critical unknown edges: canonical JARVIS/AJ runtime, Honcho DB target, memory ownership, Hermes↔AJ/JARVIS/HELIX task contracts, port 8000/8765/8788 owners.
