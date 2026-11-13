# 05 — AJ Ecosystem Phased Implementation Roadmap

## 0. Current phase: planning and documentation

**Status: UPDATED — AJ hierarchy finalized; implementation not authorized.**

Deliverables: AJ master architecture, logical workspace structure, HELIX calling architecture, partial repository catalogue, implementation sequence, decision register, and updated master project context. No code changes or installs in this phase.

## 1. Hermes preparation — user-led

The user intends to prepare Hermes before requesting the implementation master prompt. Record its version, installation type, interfaces (CLI/gateway/MCP/skills/plugins), active services, runtime location, available skills/tools, granted permissions, and user-controlled boundaries. This is a future handoff checklist, not a request to run commands now.

## 2. AJ integration discovery and contracts

After Hermes is ready, the future coding agent must read the updated master context and all planning documents, inspect actual repositories read-only, and map existing features before proposing code changes. Define AJ's central orchestration contract; AJ-to-JARVIS delegation for general and major work; AJ-to-HELIX delegation for calling/communications; AJ/Hermes adapter contract; task/result schemas; skill lifecycle and approvals; canonical memory boundaries; and cancellation/timeout/failure semantics.

Acceptance criteria: AJ retains overall authority; neither sub-agent bypasses AJ policy; Hermes does not become canonical memory; every task has traceable ownership and status.

## 3. AJ core orchestration, permissions, and audit

Implement only after contracts are approved: task lifecycle, routing policy, capability registry, permission engine, audit events, recovery/cancellation, and context builder. Decide whether AJ is a logical layer inside an existing codebase or a separately deployable component only after repository inspection and explicit approval.

## 4. Provider gateway

Define provider adapters, health/capability metadata, bounded retries/fallback, quota handling, normalized responses, and cost/usage tracking. Keep model names out of business logic. No local inference is required for current production.

## 5. AJ-governed canonical memory

Define raw event/conversation storage, structured memory, provenance/confidence, retrieval/context packaging, summaries that never delete source records, and tested backup/restore. Memory continuity must span AJ, JARVIS, HELIX, and Hermes without being owned by any model provider.

## 6. Hermes skills

Expose selected skills through an adapter; add metadata and declared permissions; implement draft/review/test/approve lifecycle; register approved skills; monitor execution. Skill success never grants new permissions.

## 7. Agent delegation and task coordination

Define parent/child tasks, progress reporting, ownership, cancellation, retry/duplicate prevention, and evidence packages. AJ routes broad/general and substantial work through JARVIS; calling and communication workflows through HELIX. Cross-domain work is coordinated by AJ. Both sub-agents retain independent identity and repository boundaries.

## 8. Desktop and browser capabilities

Evaluate one primary Linux desktop automation candidate; test on the actual GNOME Wayland environment; keep browser automation separate; add action verification and safe recovery.

## 9. HELIX phone and calling capabilities

Implement only after architecture and permissions are approved: device discovery, notifications/incoming-call events, contact resolution, dialer handoff, and remote call controls only if verified. AJ owns policy and approval oversight; HELIX owns execution. No contact guessing, auto-answer, or recording by default. Unsupported controls remain unavailable.

## 10. Optional integrations and platform expansion

Later: LMS, communications beyond calling, research, coding, video editing, Windows/macOS/mobile, robotics, and advanced device integrations. Prioritize only after core reliability is demonstrated.

## 11. Master implementation prompt gate

The final coding-agent master prompt must be produced only after: (1) AbuBakar confirms Hermes preparation is complete; (2) the updated docs are reviewed; (3) open decisions are resolved or explicitly deferred; (4) target repositories are confirmed; and (5) the first implementation phase is approved.

The prompt must require the coding agent to read all documents first, inspect repositories read-only before changes, map existing features, preserve working code/data, implement one phase at a time, test runtime behavior, stop at approval gates, never perform destructive operations without `GREEN SIGNAL`, and update documentation with evidence. It must implement AJ as the parent identity, JARVIS as the general/major-work sub-agent, and HELIX as the calling/communications sub-agent.

## 12. Immediate next milestone

No coding now. AbuBakar prepares Hermes, then returns with its status/context. Only then should the final AJ ecosystem integration and implementation master prompt be produced.
