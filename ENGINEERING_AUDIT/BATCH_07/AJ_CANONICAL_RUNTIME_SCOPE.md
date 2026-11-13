# AJ Canonical Runtime Scope

**Status:** specification only. No runtime created, no file modified in `AI_WORKSPACE/AJ`. Implementing any part of this = `A3/GREEN SIGNAL REQUIRED`.

---

## 1. Should `AI_WORKSPACE/AJ` be the canonical control-plane source?

**Yes — `RECOMMENDED`, subject to `USER DECISION REQUIRED` (U2).**

Supporting evidence:

| Evidence | Weight |
|---|---|
| It is the only component in the ecosystem whose stated and implemented purpose is control-plane behaviour: `permissions.py`, `capability.py`, `task.py`, `audit.py`, `config.py`, `contracts.py`, `orchestrator.py`, `providers.py`, `memory.py`. No other project duplicates this. | Strong for |
| Its own README explicitly disclaims being a second assistant runtime — the scope discipline the architecture needs already exists in writing. | Strong for |
| `contracts.py` already encodes the inter-component boundary types (`AgentRequest`, `ExecutionRequest`, `SkillSpec`) that a control plane must own. | Strong for |
| `config/capabilities.json` already declares HELIX/Hermes/AJ capabilities — a capability registry in embryo. | Moderate for |
| It has **no git repository**, **no entrypoint**, **no service unit**, and **zero mapped running processes**. | Gap, not disqualifier |
| Its tests have never been executed in this audit (no `pytest` available). | Gap |

**Why the gaps do not disqualify it:** a control plane with defined contracts and no process is a *library awaiting a host*, which is exactly the safe state to build from. The alternative candidates are worse: JARVIS is a desktop assistant with a 1.6 GB venv and Windows-oriented GUI code; HELIX is a voice/UI runtime. Promoting either would violate the separation the master context requires.

**Counter-position (recorded, not adopted):** one could argue AJ should stay dormant and Hermes act as de-facto coordinator, since Hermes is the only *running* multi-agent component. Rejected because Hermes is a workflow/skill execution runtime whose memory and governance semantics are exactly what the master context says must **not** be canonical, and because Hermes's Honcho write path is unproven.

---

## 2. Minimum AJ runtime boundary

The smallest future thing that can be called "AJ running". Everything here is a *specification*; none of it exists yet.

| Layer | Minimum content | Explicitly absent |
|---|---|---|
| Entrypoint | One CLI: `aj run <command>`, `aj task status <id>`, `aj capability list`. Foreground, no daemon, no scheduler, no sockets. | HTTP server, web UI, TUI, websocket bridge |
| Process model | Single process, single user, synchronous call/return. | Background daemons, worker pools, queues |
| Configuration | Layered load already designed in `config.py` (defaults < file < env < override), reading `config/aj.config.json`. | Secret storage, vault integration |
| Persistence | Append-only JSONL for tasks and audit events on local disk; SQLite for memory raw events (as already drafted in `memory.py`). | Postgres, migrations tooling, ORM |
| Interfaces | Protocol classes only: task lifecycle, permissions, audit, capability registry, provider adapter, memory contract, agent boundary. | Concrete remote transport (HTTP/gRPC) |
| Integration | Import-time-safe adapters that **probe availability and report honestly**; a missing JARVIS/HELIX/Hermes yields `available: False`, not an exception. | Auto-starting sub-agents |
| Verification | Unit tests for every interface; one end-to-end dry-run with all adapters unavailable. | Load tests, chaos tests |

**Non-negotiable:** AJ must start and complete a task with **every** sub-agent absent. Degradation is the default, not an error path.

---

## 3. What must remain outside AJ

| Outside | Reason |
|---|---|
| HELIX voice/UI/bridge/desktop code (`bridge_ws.py`, `ui/src`, `helix_desktop.py`) | Execution presentation belongs to HELIX; AJ must not grow a UI |
| JARVIS PyQt/GUI, audio devices, `desktop_input.py`, `command_center.py` | Personal-assistant surface; AJ is headless |
| Hermes agent loop, tool-calling, skills execution internals | AJ *calls* Hermes through a port; it does not become Hermes |
| Honcho schema, DDL, PG credentials | AJ owns a memory *contract*; backends own their own storage |
| Provider SDK specifics (OpenRouter/Anthropic/Gemini request shapes) | Behind a provider adapter interface |
| Local model hosting, Docker orchestration | Infrastructure layer, not control plane |

---

## 4. What AJ should coordinate

1. **Task lifecycle** — create → validate → assign → dispatch → observe → complete/fail → close, with append-only records.
2. **Delegation** — choose JARVIS vs HELIX vs Hermes vs direct provider, using the capability registry rather than hardcoded names.
3. **Policy and permission gates** — five-level permission model plus single-use approvals before any side-effecting action.
4. **Audit** — one event stream correlating task id, agent, capability, provider, model, outcome.
5. **Provider routing** — health-aware, bounded fallback, provider-independent request shape.
6. **Memory writes** — canonical raw events for everything that happens, regardless of which agent produced it.
7. **Capability truth** — advertise what exists *and is verified*, and refuse to claim what is not.

---

## 5. What AJ must NOT own directly

| Must not own | Owner instead |
|---|---|
| Conversation rendering, voice I/O | JARVIS / HELIX |
| Skill implementations | Hermes |
| Vector indexes, embedding models, session summarisation algorithms | Memory adapters (Honcho or other) — as *derived* layers |
| Provider API keys as policy | Environment/secret store; AJ reads handles, not raw secrets in code |
| OS-level automation | HELIX/agents, under AJ permission grants |
| The canonical *content* of a user conversation | Written by the producing agent, recorded by AJ — AJ is the ledger, not the author |

---

## 6. Interaction contracts

| Peer | Direction | Contract | Current reality |
|---|---|---|---|
| **JARVIS** | AJ → JARVIS `AgentRequest`; JARVIS → AJ `AgentResult` | `contracts.py` dataclasses; JARVIS is an independent repo whose runtime is not service-managed | JARVIS source exists (`AI_WORKSPACE/JARVIS`, `d93c702`); no active runtime; gateway unit misconfigured |
| **HELIX** | AJ → HELIX `AgentRequest` for calling/communications; HELIX → AJ results + audit refs | Same dataclasses; HELIX owns devices/voice, AJ owns permission to call | `helix-live` active on 8788 (voice proxy only); no AJ↔HELIX RPC exists |
| **Hermes** | AJ → Hermes `ExecutionRequest`; Hermes → AJ `ExecutionResult` | `execution.py` port + `SkillSpec` review states | Hermes running; **not attached**; no adapter implemented |
| **Honcho** | AJ memory adapter → Honcho API (derived/index only) | Contract in `CANONICAL_MEMORY_CONTRACT_v1.md` | Service healthy, 0 messages, writer unproven |
| **Provider adapters** | AJ router → provider-agnostic request → concrete SDK | `providers.py` registry + health + bounded fallback | Hermes verified on OpenRouter; AJ provider path unexercised |
| **Memory** | AJ → canonical raw store (write-first), derived layers rebuilt from it | Raw-first, provenance-labelled | Design + SQLite draft only |
| **Permissions** | Every mutating call passes `permissions.py` gate before dispatch | Level + single-use approval | Static only |
| **Task lifecycle** | Every unit of work is a task record, even delegated ones | `task.py` state machine | Static only |

**Rule:** AJ never speaks a peer's internal protocol directly. It speaks its own contract, and an adapter translates. That is what keeps sub-agents replaceable.

---

## 7. What the first foundation activation must prove

A single acceptance run that demonstrates, in order:

1. **Boots with nothing attached** — AJ starts, loads config, registers capabilities, and lists JARVIS/HELIX/Hermes/Honcho as unavailable without throwing.
2. **Refuses correctly** — a task requiring a capability that is not `verified` is rejected with an auditable reason, not attempted.
3. **Gates correctly** — a task requiring approval blocks until approval is granted, and the approval is single-use.
4. **Records correctly** — one task produces: a task record, ordered state transitions, at least one audit event with redaction applied, and one raw memory event with provenance (`agent`, `capability`, `provider`, `model`, timestamp, id).
5. **Degrades correctly** — with a stub adapter that always fails, the task fails *cleanly* with a typed error, leaving no half-written canonical record.
6. **Rebuilds correctly** — a derived summary can be regenerated from raw events, and deleting the derived layer leaves the canonical record intact.

If all six hold, AJ is a trustworthy ledger. If any fails, no sub-agent should be attached to it.

---

## 8. Explicitly deferred

- Any network listener, RPC transport, or message bus.
- Real Hermes attachment (requires A3 + Hermes contract work).
- Real JARVIS/HELIX dispatch (requires their runtimes to be stable and service-managed).
- Honcho writes from AJ (requires U1 outcome).
- Multi-user, multi-tenant, or remote access.
- Packaging/distribution, CI, git repository creation.
- GUI/voice/automation of any kind.
