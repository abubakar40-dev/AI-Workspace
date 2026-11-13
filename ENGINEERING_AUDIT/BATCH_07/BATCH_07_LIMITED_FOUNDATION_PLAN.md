# Batch 07 — Limited Foundation Implementation Plan

**PLAN ONLY. Nothing implemented. No file in `AI_WORKSPACE/AJ` (or any other project) was created or modified. Execution of any step below = `A3/GREEN SIGNAL REQUIRED`.**

---

## 1. Purpose and boundary

The smallest future change that turns AJ from *a library with contracts* into *a control plane you can actually invoke*, without attaching any sub-agent and without touching any other project.

**In scope:** one CLI entrypoint, interfaces, local persistence, honest availability probing, tests.
**Out of scope:** everything named in §7.

**Acceptance test for the whole batch:** AJ boots with nothing attached, refuses what it cannot verify, gates what needs approval, and records every step — then a full rebuild of derived memory from raw events succeeds.

---

## 2. Non-negotiable constraints

| # | Constraint |
|---|---|
| C1 | **Honcho is NOT canonical memory.** Canonical records live in AJ's own local store. Honcho, if ever wired, is an adapter behind the memory interface and may be absent. |
| C2 | No sub-agent is attached. JARVIS/HELIX/Hermes adapters must report `available: False` and AJ must function fully. |
| C3 | No process daemon, no listener, no scheduler. Foreground CLI only. |
| C4 | No network calls in the foundation. Provider adapters are interfaces with a stub, not live SDK wiring. |
| C5 | No git repository initialisation, no packaging metadata, no CI — those follow the runtime decision. |
| C6 | Every mutating operation passes the permission gate; every operation emits an audit event. |
| C7 | Existing files are extended, not rewritten: `contracts.py`, `task.py`, `audit.py`, `permissions.py`, `capability.py`, `memory.py` already define these shapes. |
| C8 | Nothing in `AI_WORKSPACE/JARVIS`, `AI_WORKSPACE/helix`, `/home/abubakargcx/helix`, `~/.hermes`, or Honcho's database is modified. |

---

## 3. The twelve interfaces

Each is a **protocol/contract plus a stub implementation**, not a working integration. "Proves" states what the stub must demonstrate.

### 1. AJ runtime entrypoint

- **Shape:** `python -m aj run <intent>`, `python -m aj task status <id>`, `python -m aj capability list`, `python -m aj audit tail`.
- **Proves:** process starts, exits non-zero on failure, returns structured output, needs no arguments to print usage.
- **Must not:** bind a socket, fork a daemon, background itself.

### 2. AJ configuration boundary

- **Shape:** layered resolution already designed in `config.py` — defaults → `config/aj.config.json` → env → explicit override; every resolved value records its source.
- **Proves:** a missing config file yields documented defaults; an invalid value fails with a typed error naming the key and source; no secret is ever echoed in an error or log.
- **Must not:** read remote config, mutate its own file, or store credentials.

### 3. AJ task lifecycle interface

- **Shape:** `create → validate → assign → dispatch → observe → complete | fail | cancel`, append-only JSONL records, every transition carrying `reason`, `actor`, and the prior state.
- **Proves:** an illegal transition is refused; a crash mid-task leaves a resumable record rather than a half-written one; a task can be closed explicitly.
- **Must not:** auto-retry a side-effecting step without a new approval.

### 4. AJ permission interface

- **Shape:** five-level model plus single-use approvals; `check(subject, action, capability, level)` returns granted/denied/needs-approval; consumption is recorded.
- **Proves:** approval is single-use (second attempt denied); expiry is honoured; every decision produces a permission event.
- **Must not:** default to allow, cache an approval across tasks, or let a peer self-grant.

### 5. AJ audit/event interface

- **Shape:** one append-only event stream with a common envelope (task id, actor, capability, provider, model, outcome, timestamp, schema version); redaction applied before persistence.
- **Proves:** redaction actually removes a planted secret; the stream is sufficient to reconstruct one task end-to-end without any derived data.
- **Must not:** log payloads containing credentials, or allow silent event loss.

### 6. AJ capability registry interface

- **Shape:** capability declarations with `verified` metadata — id, description, owning agent, required permission level, verification state, last-verified timestamp.
- **Proves:** a task requiring an unverified capability is **rejected with an auditable reason** rather than attempted; `capability list` shows verified vs unverified distinctly.
- **Must not:** advertise a capability merely because an adapter is installed.

### 7. Provider-independent adapter interface

- **Shape:** `complete(request) -> response` with a provider-neutral request/response shape; registry with health state and bounded fallback; a `StubProvider` for tests.
- **Proves:** policy-driven routing works with one stub; a dead provider is skipped, not retried forever; provider/model actually used is recorded in provenance.
- **Must not:** leak provider-specific fields into the canonical record, or hardcode a vendor.

### 8. Memory contract interface

- **Shape:** `record(event)`, `get(id)`, `query(time_range|session|task|actor)`, `rebuild_derived()`, plus adapter registration with declared capabilities.
- **Proves:** raw write succeeds with **zero** adapters registered; a derived summary can be deleted and rebuilt to parity citing the same raw ids; a purge is refused without explicit authority and is itself recorded.
- **Must not:** allow an adapter to write canonical rows, or allow "compaction" that drops raw records.

### 9. JARVIS adapter/agent boundary

- **Shape:** `AgentRequest` → JARVIS → `AgentResult` via `contracts.py`; availability probe returns `False` today; capability declarations list what JARVIS *would* provide.
- **Proves:** dispatch to an unavailable JARVIS yields a clean typed refusal, not an exception or a hang.
- **Must not:** import JARVIS code, start its processes, or read its GUI/audio state.

### 10. HELIX adapter/agent boundary

- **Shape:** as above for HELIX; capability declarations for calling/communications; availability probe reflects reality (voice proxy on 8788 exists but is not an `AgentRequest` endpoint).
- **Proves:** AJ refuses a HELIX task because no contract endpoint exists — correctly, with a reason.
- **Must not:** talk to `8788`/`4173` directly, or drive the desktop.

### 11. Hermes runtime boundary

- **Shape:** `ExecutionRequest` → Hermes → `ExecutionResult` through the `execution.py` port; `SkillSpec` review states honoured (`draft→tested→reviewed→approved`); unapproved skills refuse to run.
- **Proves:** an unapproved skill is refused; a submitted request with a malformed shape is rejected at the edge.
- **Must not:** invoke the live Hermes gateway, mutate `~/.hermes`, or trigger a paid completion.

### 12. Honcho adapter boundary

- **Shape:** optional memory adapter declaring only what is verified — today: `write_raw: unknown`, `search: unknown`. Registered but **disabled by default**.
- **Proves:** AJ runs identically with the adapter absent, disabled, and failing.
- **Must not:** be treated as canonical, be required for recall, or be enabled before `HERMES_HONCHO_VALIDATION_PLAN_v2.md` yields `RUNTIME WRITER VERIFIED`.

---

## 4. Sequencing (if and when approved)

| Step | Work | Depends on | Risk |
|---|---|---|---|
| 1 | Entrypoint + config boundary + `capability list` | U2 approval | Low — no side effects |
| 2 | Task lifecycle + audit envelope + permission gate | 1 | Low — local files only |
| 3 | Memory contract: raw write, exact/lexical query, rebuild stub | 1, 2 | Medium — schema choices harden early |
| 4 | Provider interface + `StubProvider` | 1 | Low |
| 5 | Agent boundaries 9–11 with unavailable probes | 1–3 | Low — refusals only |
| 6 | Honcho adapter shell, disabled | 3 | Low |
| 7 | Tests for every interface; end-to-end dry run with all peers absent | all | Low |
| 8 | Redaction + secret-leak test | 2 | Medium — must actually fail on a planted secret |

Steps 1–8 are one coherent unit. Splitting them yields a half-wired control plane, which is worse than none.

---

## 5. Verification the plan must satisfy before anyone attaches a sub-agent

1. Boots with nothing attached; lists four peers as unavailable; exits cleanly.
2. Refuses an unverified capability, with a reason a human can read.
3. Blocks on approval, consumes it once, denies the second use.
4. Produces for one task: task record, ordered transitions, ≥1 audit event with redaction applied, ≥1 canonical raw event with full provenance.
5. Fails cleanly against an always-failing adapter, leaving no half-written canonical record.
6. Deletes all derived data, rebuilds to parity, same source ids.
7. Runs with Honcho disabled, absent, and erroring — identical outcome.

---

## 6. Effort and evidence honesty

- No estimate is offered as a commitment: AJ's suite has **never been executed** in any batch (no `pytest` present), so even "the existing tests pass" is unverified.
- The plan deliberately reuses existing modules, so most work is wiring and hardening rather than invention.
- The first real risk is not code volume — it is whether the existing `contracts.py`/`task.py` shapes survive contact with an actual run.

---

## 7. Explicitly deferred (do not start)

GUI · voice · browser automation · desktop automation · LMS automation · phone/telephony · robotics · smart-home control · multi-agent autonomy · local LLM deployment · Docker infrastructure · production deployment · remote access · Honcho schema work · memory migration/backfill · JARVIS/HELIX refactors · repository merges · branch promotion · Obsidian navigation.

These are future layers. None of them is required to prove the control plane works, and each one would add surface that cannot be verified yet.

---

## 8. Authorization state

| Item | State |
|---|---|
| This plan | written, unimplemented |
| Creating any file in `AI_WORKSPACE/AJ` | `A3/GREEN SIGNAL REQUIRED` |
| Creating a git repo for AJ | `A3/GREEN SIGNAL REQUIRED` |
| Running the Hermes→Honcho probe (V1 paid / V2–V3 config) | `A3/GREEN SIGNAL REQUIRED` |
| Modifying `~/.hermes`, Honcho schema, JARVIS/HELIX trees, services, firewall | `A3/GREEN SIGNAL REQUIRED` |
