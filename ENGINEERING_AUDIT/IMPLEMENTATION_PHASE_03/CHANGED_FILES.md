# Changed Files

## New

| File | Purpose |
|---|---|
| `aj/locking.py` | Advisory POSIX file locks with timeout and status |
| `aj/diagnostics.py` | Read-only storage/lock/count diagnostics |
| `aj/transfer.py` | Export, dry-run import, backup, verification |
| `tests/test_phase3.py` | 32 lifecycle/concurrency/transfer/CLI/observability tests |
| `ENGINEERING_AUDIT/IMPLEMENTATION_PHASE_03/*.md` | 19 phase reports |

## Modified

| File | Change |
|---|---|
| `aj/task.py` | `CANCEL_REQUESTED`, `operation_id`, `attempts`, locked reload/append, stable legacy operation ids |
| `aj/orchestrator.py` | Attempt start/finish, honest cancel, gated retry, retry audit/memory, correlation ids in audit/memory/logs |
| `aj/capability.py` | `retry_safe` (default False), serialized |
| `aj/actions.py` | `aj.echo`/`aj.health_check` declared retry-safe |
| `aj/audit.py` | Locked append/read; `operation_id` and `attempt_id` fields |
| `aj/memory.py` | WAL, busy timeout |
| `aj/config.py` | `memory_path()`, section origins, `validate()` |
| `aj/summary.py` | Task-scoped build/verify, effective kind |
| `aj/runtime.py` | 7 new checks, temp-store isolation for health |
| `aj/__main__.py` | 9 new subcommands, exit map, JSON/quiet/verbose, summary/transfer/config |
| `README.md` | Phase 3 operations, semantics, exit codes, limitations |
| `tests/test_phase2.py` | CLI exit expectations updated to the Phase 3 contract (1 → 4/5) |

No files outside `AI_WORKSPACE/AJ` were modified except the report directory.
