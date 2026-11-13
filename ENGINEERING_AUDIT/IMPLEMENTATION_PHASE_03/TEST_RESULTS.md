# Test Results

Command:

```bash
.venv/bin/python -m pytest -q
```

Result:

```text
119 passed in 7.26s
exit 0
```

| Measure | Value |
|---|---|
| Baseline before Phase 3 | 87 passed |
| Phase 3 tests added | 32 |
| Total | 119 |
| Failures | 0 |
| Test runtime | 7.26 s |

## Coverage added

- lifecycle: success attempt, retry lineage, retry refusal, terminal refusal
- cancel: non-terminal, terminal, EXECUTING request, confirmation
- attempts: persistence and stable operation id across reload
- summary: task scope, stale detection, raw-event preservation
- concurrency: 4 processes each for tasks (15), audit (20), memory (20)
- locking: timeout and release on exception
- corruption: malformed task line reported, valid record retained
- config: origins, validation, CLI exit 5
- diagnostics: counts and lock status
- transfer: export/dry-run/import, conflict refusal, backup/verify/restore, tamper
- CLI: lifecycle, missing task/capability, JSON cleanliness, summary verify, quiet
- invariants: unknown capability, append-only audit/memory, unsafe replay
- observability: audit, memory and logs carry the same operation id and attempt id
- performance: 120 echo tasks
- health: 23 checks and named Phase 3 coverage

## Observability evidence

One execution produced:

```text
INFO aj.orchestrator task=aj_… operation=op_… attempt=att_… capability=aj.echo status=EXECUTING
INFO aj.orchestrator task=aj_… operation=op_… attempt=att_… capability=aj.echo status=COMPLETED
```

The test reads the `executed` audit event and the raw memory rows for the same
task, and asserts their `operation_id` equals the task's and their `attempt_id`
equals the persisted attempt's. Pre-attempt events legitimately have no attempt
id; they still carry the operation id.

## Isolation

```text
real task store:  7 lines before, 7 lines after
real audit store: 9 lines before, 9 lines after
```

Tests use `tmp_path` or in-memory SQLite. `--check` uses temporary stores,
including the formerly default-store lifecycle/recovery/cancel-retry checks.
