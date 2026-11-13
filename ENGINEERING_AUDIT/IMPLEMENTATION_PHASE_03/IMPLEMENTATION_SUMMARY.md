# Implementation Summary

## Lifecycle
- Added `CANCEL_REQUESTED` with explicit transitions; terminal states unchanged
  (`COMPLETED`, `CANCELLED`, `ABORTED`).
- Every execution appends an attempt record; failures retain code/message.
- Task records carry `operation_id` (generated once, stable across reloads).

## Operator controls
- `Aj.cancel_task()` returns an outcome instead of a bare boolean and explains
  refusals; `Aj.cancel()` remains the boolean compatibility wrapper.
- `Aj.retry()` checks status, budget, registry membership and `retry_safe`
  before any transition. Unsafe retries are audited and remembered.
- `aj cancel` / `aj retry` expose the outcomes and exit codes.

## Storage and concurrency
- `aj/locking.py`: `file_lock()` with non-blocking acquisition, timeout,
  guaranteed release, and `lock_status()`. POSIX-first; documented.
- Task store: exclusive lock per append, shared lock per reload.
- Audit sink: exclusive lock per append, shared lock per read.
- Memory: SQLite `timeout=30`, `journal_mode=WAL`, `busy_timeout=30000`.
- Export/backup: temporary file → `fsync` → `os.replace`.

## Transfer
- `aj/transfer.py`: deterministic, redacted export; structural validation;
  dry-run import; task-id conflict refusal before writes; duplicate memory
  signatures skipped; summary rebuild after import; SHA-256 backup manifest.

## Inspection
- `aj/diagnostics.py`: paths, bytes, counts, malformed counts, last write, last
  task/audit, memory/summary stats, lock state, configuration origins.
- `aj/config.py`: section-level origin tracking and `validate()`.
- `aj/__main__.py`: `summary`, `permissions`, `config`, `diagnostics`, `export`,
  `import`, `backup`, plus exit-code mapping.

## Observability
- Audit events now carry `operation_id` and, when an attempt exists,
  `attempt_id`. Raw-memory metadata carries both automatically.
- Execution start and terminal states log task, operation, attempt, capability
  and status at INFO on `aj.orchestrator`.
- One test asserts the task, audit event, memory rows and log line agree on the
  correlation ids; pre-attempt events keep the operation id and omit the attempt
  id rather than inventing one.

## Health
New checks: `task_locking`, `audit_locking`, `cancel_retry`, `transfer`,
`config_validation`, `storage_integrity`, `diagnostics`. Existing checks that
used the default store now use temporary directories, so `--check` cannot write
to the real store.
