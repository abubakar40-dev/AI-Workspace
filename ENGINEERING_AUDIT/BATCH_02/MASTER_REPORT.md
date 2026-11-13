# Batch 02 Master Report — Critical Infrastructure & Identity Investigation
## AJ / JARVIS / HELIX / Hermes / Honcho

**Date:** 2026-11-10  
**Mode:** Coordinated, parallel-style targeted **READ-ONLY** investigation (executed sequentially with resource awareness).  
**Output:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/ENGINEERING_AUDIT/BATCH_02/`  
**Governing context:** `AJ_Ecosystem_Planning_Documentation_v2_fixed/AJ_MASTER_PROJECT_CONTEXT.md` (read in full). Batch 01 reports reviewed.

## 1. Executive overview
Batch 02 focused on P0 identity/data-ownership/preservation/security unknowns from Batch 01. The investigation **established Honcho’s likely database backend target** (system PostgreSQL 18, port 5433, DB `honcho` via `honcho_local/honcho_server.py`; service healthy) and **separated Dental Lounge Docker Postgres instances** (5432/5434) from the ecosystem memory path. It did **not** establish the canonical AJ/JARVIS runtime source, complete memory ownership contracts, or HELIX refactor intent. High-risk areas: dirty HELIX worktree with untracked WIP and large deletions, unresolved external/exposed services (8000/8765/3389/5432/5434), and privileged gaps preventing full PG18/Honcho metadata verification. **No fixes implemented.**

## 2. Governing context and scope
- AJ = CEO/control plane; JARVIS/HELIX separate projects; Hermes separate execution/skill runtime (not CEO/canonical memory owner). Honcho = memory-related service needing verification. Provider-independent canonical memory; preservation first; GREEN SIGNAL for destructive operations.
- In scope (read-only): A Postgres/Honcho ownership, B ports/process/network, C AJ/JARVIS canonical identity, D memory ownership contract, E HELIX preservation triage, F redacted security/config inventory, correlation, prioritized plan.
- Out of scope / prohibited: all mutations, installs, service/DB changes, git cleanup, paid tests, UI automation.

## 3. Investigation methodology
- Read master context and relevant Batch 01 reports. Reused Batch 01 system/runtime snapshots where appropriate.
- Targeted read-only commands: `docker inspect`/metadata queries with env redaction, `grep`/filesystem inspection, `git status/diff --stat/log` on HELIX and backups, `ss`/`/proc`/`ps`/`systemd --user` inspection, `stat`/targeted `find` for config locations, `psql` read-only metadata attempts. Honcho/Docker metadata queried without dumping sensitive data; secrets redacted.
- Resource discipline: avoided full filesystem scans, avoided hashing large volumes/DBs, limited recursive searches, preferred targeted evidence.
- Evidence labeled VERIFIED/OBSERVED/INFERRED/UNVERIFIED/CONFLICTING/BLOCKED (see `EVIDENCE_REGISTER.md`).

## 4. Findings by workstream
### A — PostgreSQL, Honcho, database ownership
**Partially complete.** Honcho targets PG18 system cluster port 5433, db `honcho` (VERIFIED by code/config/health; runtime auth path inferred). Dental Lounge DBs are separate Docker PG17 containers/volumes/ports. Full PG18 inventory, Honcho schema/data contents, backup coverage, and extra postgres tree ownership remain BLOCKED/UNVERIFIED. Conflicting example config vs server code noted. Details: `POSTGRES_HONCHO_OWNERSHIP.md`.

### B — Port/process/network ownership
**Partially complete.** Snapshot identified owners for Hermes/bridge 3000, Honcho 8123, OmniRush 20129, helix-globe 4173, helix-live 8788, and Dental Lounge docker-proxy 5432/5434. **Exposed/unresolved:** 3389 RDP (*), 5432/5434 (0.0.0.0), 8000 and 8765 (0.0.0.0, owner UNVERIFIED), 3200 (localhost, owner UNVERIFIED). No probing/auth attempts. Details: `PORT_PROCESS_OWNERSHIP.md`.

### C — Canonical AJ/JARVIS identity
**Not resolved.** `/home/abubakargcx/JARVIS` missing. `AI_WORKSPACE/AJ` is an AJ pre-Hermes foundation (non-git, 18 `aj/*.py` modules) — aligns with AJ control-plane direction but active runtime unverified. Two dirty JARVIS backups share HEAD `cffa32d` and legacy app structure; nested appears duplicate by sample but not fully diffed. **Conclusion: CANONICAL SOURCE NOT YET ESTABLISHED.** Details: `AJ_JARVIS_CANONICAL_IDENTITY.md`.

### D — Memory ownership contract
**Partial.** Hermes has local state DBs/sessions and Honcho config/plugin signals; Honcho is healthy and implements memory/session-like API routes backed by PG18 `honcho` (inferred). Actual Hermes→Honcho writes, AJ/JARVIS/HELIX memory flows, provenance/raw-vs-derived behavior, and backup/recovery are UNVERIFIED. Multiple potential memory owners remain a P0 ambiguity. Details: `MEMORY_OWNERSHIP_AND_CONTRACT.md`.

### E — HELIX preservation triage
**Complete as triage (no remediation).** HELIX is dirty (`main...origin/main`, HEAD `e8a64cf`): 824+/6648- tracked diff, major deletions (bridge/server.py, deploy unit, diagnostics/tools, large UI areas) and **untracked WIP** including `bridge_ws.py`, `helix_desktop.py`, `ui/src`/build/package files, docs, scripts, `tools/lms_client.py`. `ui/node_modules` untracked (likely generated). Intent/equivalence UNVERIFIED; untracked files have no git backup. **Preserve entire worktree.** Details: `HELIX_PRESERVATION_TRIAGE.md`.

### F — Security/config inventory
**Partial.** Hermes sensitive files mostly 600; `honcho.json` is 664 (risk noted). Numerous secret/env/credential locations found across home/workspace (paths only, values not read). External binds and unknown services create exposure uncertainty; Honcho local API auth enforcement in server unverified; helix-live references `JARVIS_ROOT` path. Details: `SECURITY_CONFIGURATION_INVENTORY.md`.

## 5. Database ownership conclusion
- **Honcho:** uses **system PostgreSQL 18** on port **5433**, database **`honcho`**, data dir `/var/lib/postgresql/18/main` (HIGH confidence target; runtime auth path inferred). Not on Docker 5432/5434.
- **5432/5434:** Dental Lounge Docker PG17 containers/volumes (`dentallounge*` DBs) — unrelated to AJ/Hermes/Honcho memory.
- **Unresolved:** full PG18 DB/role/schema inventory, Honcho table ownership/contents (metadata-only needed), other postgres trees, backup coverage.

## 6. AJ/JARVIS canonical identity conclusion
**CANONICAL SOURCE NOT YET ESTABLISHED.** `AI_WORKSPACE/AJ` appears to be the AJ control-plane foundation candidate; legacy JARVIS backups appear to be a different historical app codebase and must be preserved. Active runtime, launcher/config ownership, and dirty backup uniqueness must be mapped before any canonical decision.

## 7. Memory ownership conclusion
**Memory ownership is NOT clear.** Honcho is a configured, healthy memory-related service with a plausible PG18 backend, and Hermes has Honcho integration signals plus independent local state. AJ has memory code but no verified runtime authority. The ecosystem lacks verified evidence of a single canonical, provider-independent memory owner with proven raw/provenance/retention behavior.

## 8. HELIX preservation assessment
**Recoverable/preservable if no destructive actions occur.** Tracked deletions are recoverable from git history in principle; **untracked source/docs/scripts are not git-backed** and are the highest preservation priority. A full approved backup including untracked files is required before any cleanup, restore, or refactor completion. Feature impact (including God’s Eye View/voice/news/eras UI surfaces) remains UNVERIFIED and needs spec-to-implementation mapping.

## 9. Security posture
- **Verified concerns:** exposed/unresolved listeners (8000/8765/3389/5432/5434), `~/.hermes/honcho.json` permissions 664, many secret-bearing file locations, unverified auth for several local/exposed services.
- **Verified strengths:** Honcho/Hermes bridge/OmniRush/helix services observed on localhost where expected; Hermes core config files mostly 600.
- **Not audited:** firewall rules in depth, auth enforcement internals, logs/argv leakage comprehensively, privilege boundaries for shell/MCP/desktop automation.

## 10. Cross-workstream dependencies
See `CROSS_WORKSTREAM_DEPENDENCY_GRAPH.md`. Canonical identity + Honcho metadata + Hermes runtime trace are prerequisite to memory contract and implementation sequencing. HELIX backup/intent clarification is prerequisite to any repo cleanup. Port ownership is prerequisite to exposure hardening.

## 11. Risks and blockers
| Risk/blocker | Severity | Status |
|---|---|---|
| HELIX untracked WIP loss / destructive cleanup | P0 | active risk; no backup approved |
| Canonical AJ/JARVIS unresolved | P0 | blocks migration/integration |
| Memory ownership unresolved; Hermes/Honcho/AJ overlap | P0 | blocks canonical memory work |
| Unknown exposed services 8000/8765 | P1/P0 | owner unknown |
| PG18 metadata inaccessible with current method | P0 blocker | A2 needed |
| Hermes→Honcho runtime flow unproven | P1 | A1/A2 follow-up |
| RDP/DB exposure intent unknown | P1 | user/ops decision |
| Honcho config permission 664 | P2 | easy fix but needs approval |

## 12. Prioritized next actions
See `PRIORITIZED_ACTION_PLAN.md`. Top 5: P0-1 HELIX backup (A4), P0-2 runtime-to-repo map (A1), P0-3 PG18/Honcho metadata audit (A2), P0-4 Hermes↔Honcho trace (A1), P0-5 identify 8000/8765/exposure intent (A1).

## 13. Approval requirements
See `APPROVAL_REQUIRED.md`. No A3/A4 actions taken. Key approvals: HELIX backup copy (A4), privileged PG metadata (A2), any state-changing hardening/restoration/migration (A3/GREEN SIGNAL).

## 14. Unresolved questions
See `UNRESOLVED_QUESTIONS.md` (U01–U10).

## 15. Overall confidence assessment
- **High:** Honcho backend target identity, Docker Dental Lounge DB separation, current service/port snapshot facts, HELIX worktree state, AJ foundation vs legacy JARVIS structural distinction.
- **Medium:** inferred Honcho runtime DB connectivity path (healthy service but no privileged schema query), duplicate nature of nested JARVIS backup (sampled), refactor interpretation of HELIX changes.
- **Low/Unverified:** canonical active AJ/JARVIS runtime, actual memory data flows/writes, Honcho schema/data ownership, unknown service purposes, backup/restore adequacy, full security posture.

**Batch 02 success criterion (partial):** database ownership for Honcho is now supported by strong evidence; AJ/JARVIS identity, memory boundaries, and full security posture are **partially evidenced but not fully resolved**. Safe next batch should focus on A1/A2/A4 blockers before any implementation.
