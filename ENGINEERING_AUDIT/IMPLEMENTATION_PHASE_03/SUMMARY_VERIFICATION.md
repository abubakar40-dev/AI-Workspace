# Summary Verification

## Operations

```bash
aj summary                     # stored rows + stats
aj summary --task <id>         # task-scoped digest, read-only
aj summary --rebuild           # store a fresh deterministic digest
aj summary --verify            # compare stored row to a fresh rebuild
```

Task-scoped summaries use kind `task_digest:<task_id>` so they do not collide
with the global digest. The digest is a pure function of raw events; no clock,
model or randomness enters the content.

## Evidence

```text
summary_id: 1
kind: task_digest  source_events: 3
{"by_kind":{"task.authorized":1,"task.completed":1,"task.created":1},…}
deterministic parity: PASS
```

`test_summary_task_scope_and_parity` appends a later event and confirms the old
summary is reported stale while raw count increases by exactly one.
`test_summary_rebuild_does_not_touch_raw_events` builds twice, compares content,
and asserts raw count is unchanged.

**Result: PASS.**
