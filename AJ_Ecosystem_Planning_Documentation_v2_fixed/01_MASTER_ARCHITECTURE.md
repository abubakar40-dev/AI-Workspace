# 01 — AJ Master Architecture

## 1. Mission

Build a reliable, modular, provider-independent personal computing ecosystem governed by **AJ**, with specialized agents, reusable skills, explicit permissions, and recoverable execution. The system reduces routine cognitive load while keeping AbuBakar in control.

This is a coordinated ecosystem, not one giant chatbot. AJ is the central identity and authority; JARVIS and HELIX remain separate projects and specialized sub-agents.

## 2. Identity and hierarchy — FINAL DECISION

### AJ — central AI identity, CEO and system manager

AJ is the overall head of the ecosystem. It owns high-level planning, task intake and routing, agent coordination, shared policy, memory governance, permission oversight, system-wide status, and final user-facing accountability. AJ may perform lightweight tasks directly where appropriate, but delegates specialized work.

The name **AJ** is final. It is associated with AbuBakar’s friend **Abdullah Ghafoor**. Do not invent an expansion of the initials or treat Abdullah Ghafoor as the project owner. The project owner/user is **AbuBakar**.

### JARVIS — general-purpose and major-work sub-agent

JARVIS remains a distinct assistant, codebase, and agent identity under AJ. Its primary domain is broad/general assistance, daily workflows, coordination, and substantial or multi-step tasks/projects. AJ routes large/general work through JARVIS when that is the appropriate execution path. JARVIS reports progress, blockers, artifacts, and evidence to AJ.

### HELIX — calling and communications sub-agent

HELIX remains a distinct assistant, codebase, and agent identity under AJ. Its primary assigned domain is phone calling, call-related workflows, and communications capabilities. Calling-related requests are routed through HELIX, subject to capability verification and user approval. HELIX reports call state and execution evidence to AJ. HELIX is not deleted, merged into JARVIS, or renamed AJ.

### HERMES — agent runtime and skill execution layer

Hermes remains a separate runtime/integration component. It may host or execute reusable skills invoked by AJ, JARVIS, or HELIX through defined adapters and permissions. Hermes is not the ecosystem's CEO, canonical memory owner, or replacement identity for any agent. Its current installation/runtime must not be changed as part of this planning update.

## 3. Routing principles

1. AJ receives the user request and remains accountable for the overall result.
2. AJ classifies intent, complexity, risk, and required capabilities.
3. Broad, general, daily, and substantial multi-step work is routed through JARVIS where appropriate.
4. Phone calls, call management, and communication workflows are routed through HELIX where appropriate.
5. Hermes is invoked as an execution/skill runtime only through explicit contracts; it does not bypass AJ policy.
6. A task may involve multiple agents, but AJ owns coordination, approval boundaries, and final reporting.
7. If a request spans domains, AJ creates a parent task and delegates bounded child tasks; agents do not silently assume authority over each other.

## 4. Shared services

These are logical capabilities and do not automatically imply separate processes, microservices, or repositories.

### 4.1 Orchestration and task lifecycle

- Accept requests through AJ.
- Classify intent, complexity, risk, and required capability.
- Select direct AJ handling, JARVIS, HELIX, Hermes skills, or a coordinated workflow.
- Create parent/child task IDs and execution records.
- Track queued, running, waiting-for-approval, completed, failed, cancelled, and recovery states.
- Return results with evidence and clear ownership.

### 4.2 Provider gateway

- Single interface for remote model providers.
- Provider/model registry and capability metadata.
- Quota/rate-limit awareness, health checks, timeout, retry, fallback, and error normalization.
- Usage/cost tracking where available.
- Configurable task-to-model routing without hard-coding provider names into business logic.

Candidate providers previously discussed include OpenRouter, Groq, Gemini, NVIDIA-hosted inference, Cloudflare, and a future local inference adapter. These are candidates, not confirmed live integrations; advertised quotas are not guaranteed.

### 4.3 Canonical memory

Canonical memory belongs to the **AJ ecosystem** and must be provider-independent. AJ governs memory policy and continuity across JARVIS, HELIX, Hermes, and future agents.

Logical layers: raw conversations/events/tasks; structured long-term memory with provenance; summaries/context indexes; and navigation/backlink interfaces such as Obsidian. Summaries never replace raw records. Memory must survive provider changes and runtime replacement. Backups require restore testing.

### 4.4 Capability registry

Every tool/adapter declares its name/version, actions, inputs/outputs, permissions, side effects, platform requirements, health, verification procedure, and failure modes. Agents discover capabilities through this registry rather than hard-coding assumptions.

### 4.5 Permission and policy engine

Risk classes: read-only, reversible, and consequential. Calling, sending, publishing, purchasing, deleting, and account/security changes require explicit authorization appropriate to the action. Agent confidence is never authorization. AJ is responsible for system-wide policy enforcement.

### 4.6 Audit, observability, and recovery

Record task IDs, requester, assigned agent, selected adapter, permission decision, approval event, outcome, and verification evidence. Do not log secrets or unnecessary personal data. Retries are bounded; cancellation is first-class; duplicate execution must be prevented for non-idempotent actions; unknown outcomes must never be reported as success.

## 5. High-level architecture

```text
                         USER / ABUBAKAR
                                |
                                v
                       AJ — CENTRAL AI / CEO
                       /        |         \
                      /         |          \
                     v          v           v
              JARVIS Agent  HELIX Agent  Hermes Runtime
              General &     Calling &    Skills / Tool
              major work    communication execution
                     \         |          /
                      \        |         /
                       +--------+--------+
                                |
                  Shared Task / Delegation API
                                |
               Policy, Permissions, Context Builder
                                |
                   Capability and Adapter Registry
                                |
             +------------------+------------------+
             |                  |                  |
       Provider Gateway   Integration Adapters   Canonical Memory
             |          Desktop/Browser/Phone/       AJ-governed
       Remote Models      Calling/Files/LMS        raw + structured
                                |
                       Audit / Recovery / Evidence
                                |
                         Results back to AJ
```

This is a conceptual component map. The preferred implementation remains a modular monolith first, with clear internal interfaces and adapters. AJ is a logical central control plane; this decision does not automatically require a new AJ repository or a new process.

## 6. Agent interaction contract

Every delegated task should carry: `task_id`, `parent_task_id`, `requester`, `assigned_agent`, `goal`, `constraints`, `allowed_capabilities`, `approval_policy`, `deadline/timeout`, `context_references`, and `expected_output_schema`.

Every result should carry: `task_id`, `agent`, `status`, `summary`, `artifacts`, `evidence`, `actions_taken`, `actions_not_taken`, `errors`, `warnings`, and `requires_user_decision`. Delegation supports progress updates, cancellation, bounded retries, and explicit failure reporting.

## 7. Boundaries and non-goals

- Do not merge JARVIS and HELIX repositories by default.
- Do not delete or retire HELIX; it is a continuing sub-agent.
- Do not rename JARVIS or HELIX to AJ; AJ is the parent identity.
- Do not create a new AJ repository or move code until repository boundaries are separately reviewed and approved.
- No Docker requirement in the current architecture.
- No local LLM in current production; preserve an adapter interface for future local inference.
- No automatic permission escalation for skills.
- No blind execution of consequential actions.
- No broad refactor before a specific phase is approved.

## 8. Decision status

| Area | Status |
|---|---|
| AJ as central AI identity / CEO / manager | FINALIZED |
| AJ associated with friend Abdullah Ghafoor; project owner AbuBakar | FINALIZED |
| JARVIS as general-purpose and major-work sub-agent | FINALIZED |
| HELIX as calling and communications sub-agent | FINALIZED |
| Preserve separate JARVIS and HELIX identities/codebases | FINALIZED |
| Hermes as reusable-skill/runtime layer | CURRENT DIRECTION |
| Modular monolith first | FINALIZED DIRECTION |
| AJ-governed, provider-independent canonical memory | FINALIZED REQUIREMENT |
| Multi-provider gateway | CURRENT DIRECTION |
| No Docker / no local LLM in current production | FINALIZED |
| Exact AJ implementation and repository boundaries | UNDER DISCUSSION |
| Exact Hermes integration contract | UNDER DISCUSSION |
| Calling implementation provider and supported controls | UNDECIDED / VERIFY LATER |
