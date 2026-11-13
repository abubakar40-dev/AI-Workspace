# Cancellation Verification

## Semantics

| State | Action | Result | Exit |
|---|---|---|---|
| RECEIVED / PLANNED / AUTHORIZED / FAILED / ESCALATED / RECOVERY_REQUIRED | cancel | `CANCELLED` | 0 |
| EXECUTING | cancel | `CANCEL_REQUESTED`, requires decision, execution **not** interrupted | 1 |
| CANCEL_REQUESTED | cancel | `CANCELLED` (operator confirmation) | 0 |
| COMPLETED / CANCELLED / ABORTED | cancel | unchanged, explained | 1 |

No signal, process kill or fake termination is performed. `CANCEL_REQUESTED` is
not terminal and is never auto-replayed by recovery.

## Evidence

```text
--- cancel idle ---
Task: aj_20261110T100527_69d40493
Status: CANCELLED
Result: Cancelled
cancel_exit=0

--- cancel completed (refused) ---
Status: COMPLETED
Result: Task is already COMPLETED; nothing was changed
cancel_completed_exit=1
```

`test_cancel_while_executing_requests_without_claiming_stop` verifies the
`CANCEL_REQUESTED` message contains "not interrupted" and that a second explicit
cancel confirms `CANCELLED`.

**Result: PASS.**
