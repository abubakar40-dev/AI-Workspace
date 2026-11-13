# Lifecycle Verification

## Transitions observed

From a fresh CLI run (`aj run --capability aj.echo`):

```text
UNDERSTANDING  routed to AJ (explicit capability)
PLANNED        explicit capability
AUTHORIZED     read-only: allowed unattended
EXECUTING      AJ:aj.echo
VERIFYING      internal action returned
COMPLETED      internal:echo
```

```text
Task: aj_20261110T100524_ddacc6c2
Status: COMPLETED
Operation: op_20261110T100524_24f89e4d
Attempt: 1/3
Attempts:
  1  COMPLETED  2026-11-10T10:05:24+05:00 -> 2026-11-10T10:05:24+05:00
```

## Attempts

- One attempt per execution; `attempt_id`, `attempt_number`, `operation_id`,
  `started_at`, `ended_at`, `status`, `failure`.
- Attempt records are appended before execution and finished on every return
  path (internal success, Hermes success, delegation, `_fail`).
- An interrupted `EXECUTING` task reloads with a `RUNNING` attempt; recovery
  starts a new attempt rather than rewriting the old one.

## Persistence

`TaskStore` reloads `tasks.jsonl` on construction. `test_attempt_model_survives_reload`
reopens a store in a new object and checks the same `operation_id`, `attempt_id`
and `COMPLETED` status.

**Result: PASS.**
