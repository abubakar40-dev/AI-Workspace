# Next Phase — Phase 03 Recommendation

## Where AJ stands

- Operable: run, list, inspect, query audit and memory, recover safely, all local.
- Persistent: tasks reload across processes; malformed records are reported.
- Bounded: only internal `replay_safe` actions execute or replay; everything external is refused.
- Tested: 87 tests, 16/16 health checks, isolated from real state.

## Recommended Phase 03: **Operator controls and lifecycle completeness** (still local)

1. **`aj cancel <task-id>` and `aj retry <task-id>`**
   - Expose the existing `Aj.cancel()`/`Aj.retry()` with explicit status preconditions and audit events.
   - Retry remains bounded by `max_attempts`; recovery stays separate.
2. **`aj summary build|list`**
   - Surface the deterministic digest; `--json` returns content and cited ids.
   - Never expose summary deletion without an explicit `--delete <id>` confirmation flag.
3. **Cross-process safety**
   - Add an advisory file lock around `tasks.jsonl` appends, or document single-writer enforcement at the CLI level.
4. **Task payload/state export**
   - `aj task <id> --export <path>` writing a self-contained JSON record (no secrets), for backup without touching the live log.
5. **Retention policy decision**
   - Whether to compact `tasks.jsonl`; if so, compaction must preserve the latest record per task and never drop transitions silently.

Acceptance: every new command is read-only or explicitly mutating, audited, tested, and usable offline with no sub-agents.

## Explicitly later (each needs A3)

| Step | Why it waits |
|---|---|
| JARVIS/HELIX `AgentRequest` endpoints | external code and running systems |
| Hermes execution adapter | HERMES GREEN SIGNAL; writer history unproven |
| Honcho adapter | canonical memory rule; writer test outstanding |
| Live provider calls | cost authorization |
| Git baseline for AJ | owner decision |
| Daemon/service/deploy | out of scope by design |

## What must not happen

- Do not widen recovery to external or side-effecting capabilities.
- Do not let a summary become a source of truth.
- Do not add a network server, queue or database to a single-user laptop foundation.
- Do not claim integration that has not been exercised end to end.
