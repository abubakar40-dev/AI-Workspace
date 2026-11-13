# AJ Ecosystem — Planning Documentation Package

**Version:** 2.1 — AJ hierarchy finalized
**Prepared:** 8 November 2026
**Project owner:** AbuBakar
**Status:** Planning and architecture only; no implementation authorized.

## Final identity and hierarchy

- **AJ** — central AI identity, CEO/system manager, orchestration and governance layer. The name is associated with AbuBakar's friend Abdullah Ghafoor. Do not invent an expansion for AJ.
- **JARVIS** — retained as a distinct general-purpose and major-work sub-agent.
- **HELIX** — retained as a distinct calling and communications sub-agent. It is not deleted, merged, or renamed AJ.
- **Hermes** — separate agent runtime and reusable-skill execution layer, not a replacement identity or CEO.

AbuBakar is the project owner. The name Abdullah has personal/religious significance for him as a self-description meaning Allah's servant, and also reflects affection for his friend Abdullah Ghafoor. Do not misidentify the project owner as Abdullah.

## Package contents

1. `01_MASTER_ARCHITECTURE.md` — AJ hierarchy, agent roles, shared services, and architecture.
2. `02_WORKSPACE_STRUCTURE.md` — logical workspace layout and repository boundaries.
3. `03_CALLING_SYSTEM_ARCHITECTURE.md` — HELIX calling design, AJ policy, permissions, and failure handling.
4. `04_GITHUB_REPOSITORY_CATALOG.md` — known project remotes and external upstream/reference repositories.
5. `05_IMPLEMENTATION_ROADMAP.md` — staged implementation plan for after Hermes is ready.
6. `AJ_MASTER_PROJECT_CONTEXT.md` — updated governing master context and development directive.
7. `AJ_MASTER_IMPLEMENTATION_PROMPT.md` — future coding-agent instructions and approval gates; not yet an execution authorization.

## Governing rules

- AJ is the parent identity and overall authority.
- JARVIS and HELIX remain separate identities and codebases as specialized sub-agents.
- General and major work routes through JARVIS; calling and communications route through HELIX.
- AJ governs task routing, shared memory, permissions, and final accountability.
- Hermes is an agent runtime/skill execution layer.
- Modular monolith first; no Docker requirement; no local LLM in current production.
- This package describes target architecture, not proof that proposed modules already exist.
- No code changes, installations, repository changes, pushes, deletions, migrations, or service changes are authorized.
- Destructive operations require explicit `GREEN SIGNAL`.
- The user will prepare Hermes first. The final implementation master prompt is gated until then.

## GitHub inventory limitation

The connected GitHub listing returned no repositories in the recorded session. The repository catalogue is partial and must not be represented as a complete private-account inventory.
