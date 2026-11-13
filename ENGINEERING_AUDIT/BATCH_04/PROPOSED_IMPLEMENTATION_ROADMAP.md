# Proposed Implementation Roadmap (Phased — NOT EXECUTED)

**Status:** Proposal only. Every phase requires prerequisites, verification, rollback, and explicit approvals (A3/GREEN SIGNAL for mutations).

## Phase 0 — Preservation and identity resolution
- **Objective:** freeze risk; establish canonical identities/runtimes.
- **Repos/systems:** HELIX backup (verified), JARVIS backups, `AI_WORKSPACE/AJ`, Hermes/Honcho runtime/config.
- **Prerequisites:** Batch 04 evidence; optional HELIX checksum hardening (A1); port 8000 privileged identification (approved read).
- **Deliverables:** approved identity map, source-only JARVIS uniqueness report, HELIX spec-to-refactor decision, exposure decisions.
- **Dependencies:** user decisions.
- **Verification:** manifests/checksums; runtime-to-repo table accepted; no unintended mutations.
- **Rollback:** n/a (read-only decisions) — preserve all copies.
- **Risks:** wrong canonical pick.
- **Complexity:** Medium.
- **Blocking decisions:** AJ/JARVIS canonical sources, HELIX intent, port 8000/exposure intent.

## Phase 1 — Core AJ foundation
- **Objective:** runnable AJ control-plane core on approved canonical source.
- **Prereqs:** Phase 0 identity decision; isolated test env.
- **Deliverables:** AJ runtime entrypoint, config validation, task/audit/memory interfaces wired minimally.
- **Dependencies:** selected repo/path.
- **Verification:** targeted tests, startup smoke, audit/event records (no production mutation).
- **Rollback:** revert to preserved state; keep backups.
- **Risks:** activating wrong codebase.
- **Complexity:** Medium-High.

## Phase 2 — Provider abstraction and agent orchestration
- **Objective:** AJ-governed provider routing; explicit JARVIS/HELIX/Hermes contracts.
- **Prereqs:** Phase 1; Hermes baseline stable.
- **Deliverables:** provider policy, agent adapters/contracts, task correlation IDs.
- **Verification:** contract tests; Hermes default path remains healthy (`PONG`-class check, no paid calls).
- **Rollback:** disable adapters; preserve prior Hermes config backups.
- **Complexity:** High.

## Phase 3 — Canonical memory
- **Objective:** implement approved memory ownership contract.
- **Prereqs:** verified Hermes↔Honcho flow/writer evidence or alternative; AJ owner decision.
- **Deliverables:** raw-first event store, provenance, summaries linked to raw IDs, rebuildable indexes, backup/restore procedure.
- **Verification:** metadata-only integration test (approved), restart persistence, provenance checks.
- **Rollback:** read-only fallback; DB backups before writes/migrations.
- **Risks:** split-brain, data loss.
- **Complexity:** High.

## Phase 4 — JARVIS integration
- **Objective:** connect independent JARVIS agent to AJ contracts.
- **Prereqs:** Phases 1–3 relevant parts; canonical JARVIS source.
- **Verification:** task delegation round-trip, audit trail.
- **Complexity:** Medium-High.

## Phase 5 — HELIX integration
- **Objective:** connect HELIX (post-refactor decision) to AJ contracts.
- **Prereqs:** HELIX intent/spec map; disposable-copy validation.
- **Verification:** bridge/UI/service smoke tests, feature checklist vs spec.
- **Complexity:** High (due current dirty/refactor state).

## Phase 6 — Hermes skill/workflow integration
- **Objective:** formalize Hermes as governed execution runtime/skill provider.
- **Verification:** scoped workflow tests; memory/audit contract compliance.
- **Complexity:** Medium.

## Phase 7 — Permissions, reliability and recovery
- **Objective:** runtime enforcement, supervised services, backup/restore drills.
- **Verification:** policy tests, restart/recovery drills (approved/isolated).
- **Complexity:** Medium-High.

## Phase 8 — Optional integrations and advanced capabilities
- **Objective:** LMS, OCI, extra channels, advanced automation features — **only if core stable and approved**.
- **Complexity:** Variable.

**No implementation prompts generated. No source modified in Batch 04.**
