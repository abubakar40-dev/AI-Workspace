# Recovery Verification

Recovery was re-checked after the attempt and lock changes.

## Policy

- Scan is read-only.
- Replay requires an internal adapter **and** `replay_safe=True`.
- Unsafe or unknown capabilities become `RECOVERY_REQUIRED`; recovery refuses
  and exits non-zero for an explicit request.
- `CANCEL_REQUESTED` is classified as requiring a human, never replayed.
- Replay retains the task id and history and appends recovery events.

## Evidence

After seeding a failed `jarvis.web_search` task:

```text
--- recover ---
aj_20261110T100527_e44f6031  FAILED  recovery_required  capability is not an internal action
```

`test_unsafe_replay_is_refused` confirms the finding decision and that
`recover(task_id)` returns `ok=False`. Existing Phase 2 tests still cover safe
replay to `COMPLETED`.

**Result: PASS.**
