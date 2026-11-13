# AJ/Hermes/Honcho Memory Ownership & Contract (Workstream D)

**Status:** Partial. Actual runtime data flows are **not fully traced**; storage backends and write paths have strong signals but key contracts remain UNVERIFIED.

## Intended direction (master context, not implementation proof)
- AJ ecosystem owns/governs canonical memory (provider-independent). Hermes is execution/skill runtime, not CEO/canonical memory owner. Honcho is an existing memory-related service. Raw records preserved; summaries traceable/provenance retained.

## Actual implementation signals (VERIFIED/OBSERVED)
| Component | Observed role/signal | Storage/signal | Read/Write (evidence) | Confidence |
|---|---|---|---|---|
| Hermes | Gateway/agent runtime; has `~/.hermes/plugins/honcho`, `honcho.json` (URL 8123, env local, key redacted), local state DBs (`state.db`/WAL/SHM, `projects.db`, `kanban.db`), `sessions/` request dumps, session state | Local SQLite/files under `~/.hermes` | Hermes→Honcho **CONFIGURED/POSSIBLE**; actual runtime writes/reads **UNVERIFIED** | OBSERVED |
| Honcho server | Local service healthy, `database: connected`; workspace code `honcho_local/honcho_server.py` implements v3-style workspace/peer/session/scope API routes; connects to PG18 port 5433 DB `honcho` (code evidence) | **Likely** system Postgres 18 `honcho` DB on `/var/lib/postgresql/18/main` | API can receive/write memory/session data (by design of routes) — **actual usage by Hermes/AJ/JARVIS/HELIX UNVERIFIED** | VERIFIED service + code target; runtime data flow UNVERIFIED |
| AJ foundation (`AI_WORKSPACE/AJ`) | Contains `aj/memory.py` module (ports/adapters style per README) | Codebase present; no confirmed active process/DB | **UNVERIFIED** whether instantiated/canonical in runtime | OBSERVED code only |
| JARVIS legacy backups | contain `memory/` dirs (structure hint) | unknown active DBs | **UNVERIFIED** | OBSERVED |
| HELIX | memory implementation not mapped in this pass | unknown | **UNVERIFIED** | UNVERIFIED |
| Obsidian | master doc references as navigation layer; vault presence/active integration not verified | unknown | **UNVERIFIED** | UNVERIFIED |

## Ownership matrix (current evidence)
| Component | Data type | Read access | Write access | Storage | Canonical/derived/cache | Provenance | Evidence |
|---|---|---|---|---|---|---|---|
| Hermes local state | sessions/agent state/request dumps/kanban/projects | Hermes (OBSERVED) | Hermes (OBSERVED) | `~/.hermes/state*.db`, `sessions/*`, `*.db` | **UNVERIFIED** (likely operational/derived/session) | partial/UNVERIFIED | filesystem |
| Honcho | workspaces/peers/sessions/scopes/messages-like API domain (per routes) | clients via API (UNVERIFIED who) | clients via API (UNVERIFIED who) | PG18 `honcho` DB (INFERRED) | **candidate canonical memory store**, but not proven canonical for AJ ecosystem | UNVERIFIED | server code, health |
| AJ memory module | intended canonical interface/records (target) | UNVERIFIED | UNVERIFIED | UNVERIFIED | target canonical | target requirement | AJ README/code presence |
| JARVIS/HELIX memory | project-specific memory (unknown) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | not mapped |

## Flow tracing (required paths)
| Flow | Status | Evidence / gap |
|---|---|---|
| User conversation → Hermes → Honcho | **Partially implemented / UNVERIFIED** | Hermes has Honcho config/plugin signals; Honcho healthy with DB target. No captured runtime trace proving Hermes writes conversation data to Honcho. |
| User task → AJ → JARVIS/HELIX | **Documentation/foundation only / UNVERIFIED** | AJ foundation has contracts/orchestrator concepts; active runtime wiring unverified. |
| JARVIS/HELIX task result → AJ | **UNVERIFIED** | no runtime evidence. |
| AJ memory retrieval → agent context | **UNVERIFIED** | AJ memory code exists; integration unverified. |
| Raw event → summary/derived memory | **UNVERIFIED** | Honcho/AJ/Hermes capabilities unknown in practice. |
| Backup → recovery path | **UNVERIFIED** | no verified backup/restore evidence. |

## Architectural risks / possible violations (UNVERIFIED unless noted)
- **Multiple potential memory owners:** Hermes local state, Honcho, AJ memory module, legacy JARVIS/HELIX memory stores — **P0 ambiguity**.
- Hermes could become unintended memory authority if it persists independently of AJ/Honcho contracts (UNVERIFIED).
- Provider independence: inference now separated from Honcho service (good signal), but memory canonical ownership not proven.
- Raw-vs-summary, provenance, retention/deletion, dedupe, backup/restore: **UNVERIFIED**.

## Safe next steps (read-only, approval-gated for privileged DB access)
1. Inspect Hermes honcho plugin implementation (`~/.hermes/plugins/honcho` and installed package) and Hermes config flags for whether Honcho integration is enabled and what it sends.
2. With approved admin access, run **metadata-only** queries on PG18 `honcho` DB (tables, row counts, recent timestamps by table name patterns, schema only) — no content dump of messages.
3. Identify active JARVIS/HELIX memory stores and whether they reference Honcho, Hermes state, or local DBs.
4. Draft the **observed vs target** contract: AJ canonical raw event/task/conversation store; Honcho as adapter/service only if proven compatible; Hermes session state as operational cache unless explicitly promoted.
