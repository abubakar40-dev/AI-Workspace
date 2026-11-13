# Task Persistence Verification — Phase 02

## Design

`TaskStore` keeps an in-memory index and appends one full record per change to `<data_dir>/tasks.jsonl`:

```json
{"reason": "transition", "task": { "task_id": "...", "status": "...", "events": [...], ... }}
```

- **History is append-only.** A record is never rewritten; later lines supersede earlier ones on load.
- **Reload is automatic.** `TaskStore(persist_dir)` calls `reload()` at construction.
- **Last record wins.** For each `task_id`, the last successfully parsed line becomes the current record, and that record carries the complete transition list.
- **Corruption is reported, not repaired.** Malformed JSON or an unknown status is appended to `load_errors` with its line number; valid records still load; the file is untouched.

## Verified behaviours

| Behaviour | Evidence |
|---|---|
| Create → execute → persist | CLI `run` wrote `tasks.jsonl`; `aj task` in a new process displayed `COMPLETED` and all six transitions |
| Reload after restart | `test_task_survives_a_process_style_restart`: a second `TaskStore(directory)` returns the same id, status, `request_payload` and event list |
| Failure detail survives | `test_failed_task_is_persisted_with_its_error`: reloaded record is `FAILED` with `execution_failed` |
| Request payload survives | reloaded `request_payload == {"text": "persist me"}` (needed for safe replay) |
| Corrupted line | `test_corrupted_record_is_reported_and_history_is_not_deleted`: 1 valid task loads, 2 errors reported, file still has 3 lines |
| Filtering | `aj tasks --status AUTHORIZED` / `--status PLANNED` each returned exactly the matching task |
| Full record inspection | `aj task <id>` prints goal, requester, owner, capability, timestamps, summary, errors and every transition |

## Defect found and fixed

The failure path persisted the record during the `FAILED` transition and then added the error object without saving again; a reloaded task therefore had no error detail. Completed summaries had the same problem. Fixed by saving after late mutations in `_fail`, internal completion, Hermes completion and delegated results. Covered by the reload test above.

## Schema additions

| Field | Purpose |
|---|---|
| `request_payload` | exact arguments, so a replay-safe task can be replayed faithfully |
| `RECOVERY_REQUIRED` | persisted marker for a task a human must handle |

## Limits

- No cross-process write lock; two concurrent writers to `tasks.jsonl` could interleave lines. Single-user foreground use is assumed.
- The store does not compact; the file grows with each transition. No retention policy yet.
- `aj tasks` reads the file even when `runtime.persist_tasks` is false (read-only, no file is created).
