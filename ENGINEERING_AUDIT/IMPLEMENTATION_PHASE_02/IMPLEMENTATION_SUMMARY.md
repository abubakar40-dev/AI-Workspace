# Implementation Summary — Phase 02

## Transformation

Before: a runnable foundation whose task state lived only in the current process.
After: an operable local control plane where a task survives a restart, can be inspected and queried, and can be recovered only when that is provably safe.

```
CLI → orchestrator → permissions → internal action → audit + raw memory
    → tasks.jsonl (append-only) → fresh process reload → inspect/query
    → recover (only replay-safe) → summary rebuild (derived)
```

## Work completed

| Requirement | Implementation |
|---|---|
| A. Operational CLI | `run`, `tasks`, `task`, `audit`, `memory`, `capabilities`, `recover`; `--json`; non-zero exits on refusal |
| B. Persistent task store | `TaskStore` reloads `tasks.jsonl` on construction; `save/update/query`; request payload stored |
| C. Memory inspection | `aj memory` over `MemoryStore.events()` with `--task`, `--type`, `--limit`, provenance intact |
| D. Recovery/resume | `RecoveryManager` + `Aj.recover`; `RECOVERY_REQUIRED`; only internal `replay_safe` actions replay |
| E. Derived-summary rebuild | `aj/summary.py`; deterministic content; delete/recreate with raw hash unchanged |

## Key design decisions

1. **Append-only JSONL, last record wins.** No database. A reload replays every line and keeps the latest record per task id, preserving the full transition list in that record. Malformed lines are reported and skipped, never rewritten.
2. **Replay is opt-in, per capability.** `CapabilitySpec.replay_safe` defaults to `False`. Only `aj.echo` and `aj.health_check` declare `True`. Recovery checks capability registration, internal adapter and the flag — in that order — before doing anything.
3. **Unsafe recovery is a recorded state, not an exception.** A refused task moves to `RECOVERY_REQUIRED`, `requires_user_decision=True`, with an audit `recovery_refused` event and a `task.recovery_refused` raw event. This is visible in `aj tasks`.
4. **Derived summaries are pure functions of raw events.** No clock, no model, no provider. The digest includes event ids and counts; rebuilding appends a new summary row but changes nothing canonical.
5. **`run` is not a shell.** Only internal adapters execute. `aj.delegate` (adapter `aj.orchestrator`) and every JARVIS/HELIX capability are refused before execution.
6. **Query commands are read-only.** `tasks`/`task` reload the log; `audit` reads JSONL; `memory` opens the store only if the file exists. None writes to history.

## Defect found and fixed during verification

The failure path transitioned the task to `FAILED` (persisting the record) and only then called `record_error()`. Reloading showed no error detail. Completed summaries had the same late-write issue. Fixed by explicitly saving the record after late mutations (`_fail`, internal completion, Hermes completion, delegated result). The regression test reloads a failed task and asserts the error code survives.

## Deliberate non-goals

- No cancel/retry CLI (the orchestrator API exists; exposing it needs its own policy review).
- No summary CLI.
- No cross-process lock on `tasks.jsonl` (single-user, foreground assumption documented).
- No external adapter, provider call, Honcho, daemon, container or deployment.
