# AJ Ecosystem — Master Engineering Report (Batch 01)

**Date:** 2026-11-10  
**Authorized scope executed:** read-only inspection, safe health checks, non-destructive report generation in `AI_WORKSPACE/ENGINEERING_AUDIT/BATCH_01/`. **Not authorized/executed:** destructive ops, config/credential/DB changes, installs/updates, service restarts, Docker/Postgres removal, migrations, paid API calls, Git history rewrites.  
**Governing reference:** `AI_WORKSPACE/AJ_Ecosystem_Planning_Documentation_v2_fixed/AJ_MASTER_PROJECT_CONTEXT.md` (read fully). Preserved distinctions: AJ CEO/control plane identity; JARVIS and HELIX separate projects/sub-agents; Hermes separate runtime; provider-independent canonical memory; no Docker/local LLM in current production; GREEN SIGNAL for destructive operations.

## 1. Cross-workstream synthesis
| Area | Verified/Observed | Main gaps/risks |
|---|---|---|
| System/runtime | 8GB-class host, swap 2.4/4GiB used, root 83%; Hermes gateway+bridge, Honcho, OmniRush running; Docker+multiple Postgres trees present | Service ownership, DB backend mapping, exposed-port owners, swap cause trend |
| Workspace/migration | AI_WORKSPACE mounted; `/home/JARVIS` missing; `helix` home dirty; AJ foundation and JARVIS backups in workspace; Honcho runs from workspace | Canonical active JARVIS/AJ unknown; full checksum/path/WAL/profile/venv migration proof incomplete |
| Hermes | v0.23.0, OpenRouter default verified, fallback capability exists in code/docs, Honcho config present (key redacted) | Fallback not configured; Hermes↔Honcho memory contract unverified; MCP/skills/sessions not fully mapped |
| Providers | OpenRouter baseline works; Hermes supports many provider plugins | Free quotas/limits time-sensitive UNVERIFIED; Groq/Cloudflare target support unclear; no approved live tests |
| Memory/Honcho | Honcho healthy/DB connected; separate from inference | Canonical ownership/provenance/duplication/backup-restore UNVERIFIED; Honcho DB backend unknown |
| JARVIS/AJ | AJ pre-Hermes foundation exists (README: ports/adapters, tests claimed); legacy JARVIS backups dirty | Canonical active app unknown; feature/runtime/test health UNVERIFIED |
| HELIX | Active git repo present but worktree has modifications/deletions affecting bridge/deploy/tools/UI | Feature preservation/health UNVERIFIED; regression risk from deletions; manifests unclear |
| Desktop automation | Not tested | Wayland/AT-SPI/portal/computer-use compatibility unknown; master doc requires controlled tests |
| Security | Secret locations observed, no secrets exposed; some 0.0.0.0 listeners | AuthZ/permission gates, external exposure risk, secret logging unverified |
| Integration/architecture | Target model clear in master doc | Actual AJ↔JARVIS↔HELIX↔Hermes contracts/runtime wiring unverified |
| Testing/recovery | Health checks + prior Hermes smoke test only | No suite execution; recovery/backup restore untested |

## 2. Shared problems / coupling
- **Canonical-path ambiguity** affects migration, testing, security scanning, and feature audits (JARVIS missing home path; AJ/JARVIS copies).
- **Data-plane ambiguity** (multiple Postgres trees + Honcho “connected”) affects memory correctness, backup, and future consolidation.
- **Single verified inference path** (OpenRouter) is a reliability/cost risk until an approved fallback strategy is validated.
- **Dirty repos/uncommitted work** (HELIX, backups, honcho_local) create preservation and regression-analysis burden.
- **Hardware pressure** (8GB RAM, swap in use, heavy desktop/Electron/browser load) constrains always-on multi-agent/runtime design.

## 3. What is safe now vs approval-gated
- **Safe now (A):** read-only mapping/inventory, redacted security reports, design docs, metadata migration comparison (careful around active DB/WAL), safe no-side-effect health checks, test inventory.
- **Approval-gated (B/C/D):** config/credential changes, fallback edits, installs, service restarts, DB writes/migrations, Docker/Postgres changes, path migration/symlinks, UI automation clicks/types, paid API tests, Git history operations, deletions.

## 4. Highest-value first batch
Run together as read-only: Postgres/Honcho DB owner map; canonical JARVIS/AJ identification; Hermes↔Honcho memory contract audit; HELIX dirty-worktree triage; exposed-port ownership/auth posture; redacted security inventory. See `PRIORITIZED_ROADMAP.md`.

## 5. Evidence index
Primary snapshots: `_system_snapshot.txt`, `_runtime_snapshot.txt`, `_docker_postgres_snapshot.txt`, `_hermes_honcho_omnirush.txt`. Reports: `EXECUTIVE_SUMMARY.md`, `SYSTEM_AUDIT.md`, `WORKSPACE_MIGRATION.md`, `JARVIS_AUDIT.md`, `HELIX_AUDIT.md`, `HERMES_AUDIT.md`, `PROVIDER_RESEARCH.md`, `MEMORY_HONCHO_AUDIT.md`, `DESKTOP_AUTOMATION.md`, `SECURITY_AUDIT.md`, `INTEGRATION_ARCHITECTURE.md`, `TECHNOLOGY_GOVERNANCE.md`, `TESTING_RECOVERY.md`, `DEPENDENCY_GRAPH.md`, `PRIORITIZED_ROADMAP.md`, `APPROVAL_REQUIRED.md`.

*No secrets included. Findings labeled VERIFIED/OBSERVED/INFERRED/UNVERIFIED/RECOMMENDED/REQUIRES USER APPROVAL where applicable.*
