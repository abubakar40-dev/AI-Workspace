# Memory Verification

- Raw events remain canonical and append-only; no delete API exists.
- `memory` reads newest-first with task/kind filters and stats.
- WAL mode + busy timeout allow independent local writers.
- `verify()` re-checks every summary citation.

## Evidence

80 events written by 4 processes:

```text
events=80  unique_ids=80  verify.ok=True
```

CLI run for one task:

```text
ID 3  task.completed  aj_20261110T100524_ddacc6c2  aj.echo completed
ID 2  task.authorized aj_20261110T100524_ddacc6c2  read-only: allowed unattended
ID 1  task.created    aj_20261110T100524_ddacc6c2  run aj.echo
```

Append-only invariant test captures the audit file bytes and raw count, runs
readers and a summary build, then asserts neither changed.

**Result: PASS.**
