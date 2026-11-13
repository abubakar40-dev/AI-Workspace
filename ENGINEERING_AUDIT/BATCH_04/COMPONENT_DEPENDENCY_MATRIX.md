# Component Dependency Matrix (Proposed, evidence-grounded)

| Subsystem | Existing implementation (evidence) | Runtime evidence | Proposed owner | Dependencies | Missing components | Risks |
|---|---|---|---|---|---|---|
| Identity/orchestration | AJ foundation `orchestrator/task/config/agents` (static) | **No active AJ runtime mapped** | AJ | canonical repo identity, config/launcher | runtime entrypoint, deployment/supervision | identity unresolved |
| Hermes execution runtime | Hermes agent/gateway/bridge running | **VERIFIED running** | Hermes (runtime) / AJ governance | providers, plugins, local state | clear AJ/Honcho memory contract | may become de facto owner |
| Honcho memory service | `honcho_local` server + PG18 `honcho` DB schema verified | service healthy; DB metadata verified | AJ-governed adapter/candidate | PG18, auth/config, writers | verified write path, provenance, retention, backup | writer unknown; 0 messages |
| AJ canonical memory | `aj/memory.py` SQLite raw/summaries design | **UNVERIFIED runtime** | AJ | storage path, integration hooks | runtime wiring, migration/adapters, tests in situ | split-brain memory |
| JARVIS assistant | legacy backups; missing `/home/abubakargcx/JARVIS` | **no mapped runtime** | JARVIS (independent project) | identity resolution, model/provider, memory contract | canonical source/runtime | stale/fragmented copies |
| HELIX execution agent | helix repo + live/globe services; dirty refactor | live/globe **running**; feature completeness UNVERIFIED | HELIX (independent project) | bridge/UI state, deps, memory contract | spec mapping, refactor completion, tests | WIP loss/regression (backup mitigated) |
| Provider abstraction | Hermes OpenRouter default verified (prior); AJ `providers` code present | Hermes inference path verified | AJ policy + Hermes/agents adapters | keys/config, routing rules | unified ecosystem policy | provider coupling |
| Permissions/approvals | AJ `permissions/capability` code | UNVERIFIED runtime | AJ | audit log, UI/CLI gates | enforcement wiring | unsafe actions |
| Audit logs | AJ `audit.py` concept; systemd journals | partial | AJ + components emit structured events | storage, schema | unified provenance | weak forensics |
| Task lifecycle | AJ `task.py` JSONL; Hermes sessions | AJ task runtime UNVERIFIED | AJ | orchestrator, agent adapters | end-to-end tracing | orphaned tasks |
| Desktop/browser automation | HELIX tools deleted/untracked WIP; Hermes skills/tooling | partial/UNVERIFIED | HELIX/Hermes by capability | permissions, OS access | verified safe harness | privilege/safety risk |
| Backup/restore | HELIX backup verified (scope); Honcho/Hermes/AJ backups UNVERIFIED | partial | ops/AJ policy | storage targets, manifests, drills | automated/verified restores | data loss |
| Config management | scattered (`~/.hermes`, repo configs, systemd, env files) | observed | AJ target governance | secret handling, validation | inventory + ownership | drift/secrets exposure |
