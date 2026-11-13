# Proposed AJ Ecosystem Architecture (Evidence-Grounded Proposal — NOT APPROVED/IMPLEMENTED)

## Target direction (to validate, not assume implemented)
- **AJ = Central Manager/Orchestrator** (control plane, policy, task routing, canonical memory governance)
- **JARVIS = Personal Assistant Agent** (independent project/repo/identity)
- **HELIX = Advanced Execution Agent** (independent project/repo/identity)
- **Hermes = Reusable Workflow/Skill Execution Runtime** (separate runtime; not CEO/canonical memory owner)
- **Honcho = Memory-related service candidate** (validated backend/schema; writer/contract still unproven)

## Design principles
- Modular monolith/control-plane first; **no microservices without evidence**.
- Provider-independent canonical memory: raw-first, append-oriented history; derived summaries linked to raw IDs; rebuildable indexes; provenance/timestamps; backup/restore.
- Keep JARVIS and HELIX as **independent repositories/identities**; AJ coordinates, does not absorb.
- Preservation and explicit approval before mutations.

## Subsystems
### 1) Identity & orchestration (AJ)
- *Existing:* AJ foundation modules (permissions/capability/task/audit/config/orchestrator/providers/memory). *Runtime:* unverified. *Owner:* AJ. *Missing:* active runtime, repo identity decision, adapter wiring. *Risk:* wrong canonical source.

### 2) Agent communication
- *Existing:* concepts/contracts in AJ; Hermes gateway active; no verified AJ↔JARVIS↔HELIX runtime bus. *Owner:* AJ-defined contracts. *Missing:* verified transport/protocol, task/result schemas. *Risk:* ad hoc coupling.

### 3) Task lifecycle
- *Existing:* AJ task model/JSONL; Hermes sessions. *Owner:* AJ canonical task state (target). *Missing:* end-to-end correlation IDs/provenance across runtimes.

### 4) Provider abstraction & routing
- *Existing:* Hermes OpenRouter default verified; AJ providers abstraction in code. *Owner:* AJ policy, adapters in runtimes. *Missing:* unified policy/enforcement.

### 5) Memory ownership & persistence
- *Existing:* Honcho PG18 `honcho` schema verified (capable); Hermes configured/plugin; AJ SQLite memory design in code. *Owner (target):* AJ-governed canonical store. *Missing:* verified writers, contract, provenance, retention, backups. *Risk:* split-brain/hidden ownership.

### 6) Capability/skill registry
- *Existing:* AJ capability/skill concepts; Hermes skills/plugins. *Owner:* AJ registry + runtime adapters. *Missing:* unified registry and permission checks.

### 7) Permissions & approval policies
- *Existing:* AJ permission/capability modules (static). *Owner:* AJ. *Missing:* runtime enforcement, GREEN SIGNAL workflow integration.

### 8) Audit logs
- *Existing:* AJ audit module; system journals. *Owner:* AJ + components emit structured events. *Missing:* unified, queryable audit trail.

### 9) Error handling & recovery
- *Existing:* partial in components. *Missing:* supervised restart policies, idempotency, dead-letter/escalation paths.

### 10) Configuration management
- *Existing:* scattered configs/envs/systemd. *Owner (target):* documented AJ-governed config map with secret hygiene. *Missing:* canonical inventory and validation.

### 11) Runtime supervision
- *Existing:* Hermes/HELIX user services; Honcho launched manually/background in observed state. *Missing:* declared desired-state supervision map.

### 12) Backup & restore
- *Existing:* HELIX backup verified (scope). *Missing:* Honcho PG18/AJ/Hermes/JARVIS backup+restore drills.

### 13) Desktop/browser/PC automation
- *Existing:* HELIX deleted tools + untracked WIP; Hermes/tooling capabilities. *Owner:* capability-scoped (HELIX/Hermes) under AJ permissions. *Missing:* verified safe harness.

### 14) Optional connectors/future portability
- Keep separate from core: LMS, OCI, extra channels, future platforms. Do not treat as approved core requirements.

## Recommended implementation order (proposal)
1. Resolve identity + preservation decisions (no code moves without approval).
2. Resolve memory contract with verified evidence (Honcho writer/flow, AJ owner).
3. Harden/clarify runtime supervision and exposure (read-only first).
4. AJ minimal runtime/orchestration on canonical sources.
5. Integrate Hermes/JARVIS/HELIX via explicit contracts and tests.
