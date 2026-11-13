# Retry Verification

## Policy

- Only `FAILED` tasks; terminal tasks raise `calling_invalid_state`.
- Budget: `attempt >= max_attempts` escalates instead of executing.
- Capability must exist and declare `retry_safe=True`; default is `False`.
- Refusal: audited (`retry_refused`), remembered (`task.retry_refused`), task
  marked `requires_user_decision`, no attempt started, exit 6.
- Allowed: task id retained, attempt appended, original failure retained,
  `retry_started` audited and `task.retry` remembered.

## Evidence

Safe retry of a synthetic first-attempt failure:

```text
--- retry safe ---
Task: aj_20261110T100527_dcd8c585
Capability: aj.echo
Status: COMPLETED
Summary: aj.echo completed
retry_exit=0

--- retried task attempts ---
  1  FAILED     … failure=execution_failed
  2  COMPLETED  …
```

Unsafe retry of `jarvis.web_search`:

```text
Summary: Retry refused: capability is not declared retry-safe
retry_unsafe_exit=6
```

`test_retry_preserves_task_id_and_history` and
`test_retry_is_refused_for_unmarked_capability` cover the same contract in the
unit suite.

**Result: PASS.**
