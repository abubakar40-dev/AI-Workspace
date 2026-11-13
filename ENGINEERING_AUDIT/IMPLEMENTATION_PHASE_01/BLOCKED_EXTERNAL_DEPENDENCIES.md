# Blocked External Dependencies

**Nothing in this list blocked Implementation Phase 01.** Each item blocks a *future* integration step and requires an owner decision. None was worked around, and no external system was modified.

---

## 1. JARVIS task endpoint

```
BLOCKED EXTERNAL DEPENDENCY: AI_WORKSPACE/JARVIS
WHY: the AJ AgentRequest contract has no agreed HTTP task endpoint on the JARVIS side;
     the bridge is WebSocket-based and its protocol is not an AJ contract
REQUIRED CHANGE: define and expose POST /aj/task (or an agreed equivalent) in JARVIS
RISK: touching a mature personal assistant; protocol churn; JARVIS has no active runtime
A3/GREEN SIGNAL REQUIRED: YES
```

AJ behaviour meanwhile: `HttpAgentAdapter` probes and returns `rejected` with `agent_unavailable`; never a hang or a false success.

## 2. HELIX AgentRequest endpoint

```
BLOCKED EXTERNAL DEPENDENCY: AI_WORKSPACE/helix
WHY: helix-live exposes a voice/WebSocket path, not an AJ task endpoint
REQUIRED CHANGE: an AJ-facing task contract in HELIX, under its own ownership
RISK: HELIX is the active runtime on 8788; changes affect a running system
A3/GREEN SIGNAL REQUIRED: YES
```

## 3. Hermes execution runtime

```
BLOCKED EXTERNAL DEPENDENCY: Hermes (installed, running, not attached)
WHY: attaching requires a HermesExecutionAdapter and the owner's HERMES GREEN SIGNAL
REQUIRED CHANGE: adapter implementation + skill review states proven end to end
RISK: Hermes writes to its own stores; its Honcho writer path is unproven
A3/GREEN SIGNAL REQUIRED: YES
```

AJ behaviour meanwhile: execution port reports `NOT ATTACHED`; `hermes.execute_skill` is declared `planned` and blocked before execution.

## 4. Honcho as memory adapter

```
BLOCKED EXTERNAL DEPENDENCY: Honcho PostgreSQL (localhost:5433, db honcho) + ~/.hermes
WHY: canonical memory is AJ raw-first; Honcho is optional and unproven (0 messages)
REQUIRED CHANGE: an adapter implementing the AJ memory interface, plus a validated writer test
RISK: database writes, provider coupling, an unproven writer
A3/GREEN SIGNAL REQUIRED: YES
```

AJ behaviour meanwhile: Honcho is not imported, configured or contacted. Raw memory works with zero adapters.

## 5. Live provider calls

```
BLOCKED EXTERNAL DEPENDENCY: OpenRouter / Groq / Gemini / local model
WHY: no paid call is authorized and no credential is used in this phase
REQUIRED CHANGE: an owner-approved test call or a local model
RISK: cost, quota, and the endpoint-confusion failure seen in the Honcho misroute
A3/GREEN SIGNAL REQUIRED: YES
```

AJ behaviour meanwhile: `MockProvider` and injected transports prove the boundary offline.

## 6. Git history for AJ

```
BLOCKED EXTERNAL DEPENDENCY: none (owner decision)
WHY: AI_WORKSPACE/AJ is not a git repository
REQUIRED CHANGE: owner decision to init/track AJ, then a first baseline commit
RISK: irreversible history choices; repository conventions affect JARVIS/HELIX workflows
A3/GREEN SIGNAL REQUIRED: YES
```

No `git init`, commit, reset, clean or push was performed.
