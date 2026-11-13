# Memory Query Verification — Phase 02

## Canonical model

| Layer | Storage | Authority |
|---|---|---|
| Raw events | `<data_dir>/memory.sqlite3`, `raw_events` table, append-only | **Canonical** |
| Summaries | same database, `summaries` table, cites raw ids | Derived |
| Honcho / providers | not wired | Absent |

`MemoryStore` still exposes no delete API for raw events. The CLI opens the store only when the file already exists.

## `aj memory` verified

Command against the isolated config after one run:

```
   ID  WHEN                KIND               TASK              PREVIEW
    3  …09:46:12+05:00     task.completed     aj_…acd3d291      aj.echo completed
    2  …09:46:12+05:00     task.authorized    aj_…acd3d291      read-only: allowed unattended
    1  …09:46:12+05:00     task.created       aj_…acd3d291      run aj.echo
```

Provenance retained per event: `id`, `at`, `kind`, `source`, `task_id`, `content`, `meta`.

| Option | Verified |
|---|---|
| `--task <id>` | returned only that task's events, all with matching `task_id` |
| `--type task.completed` | filters by event kind |
| `--limit N` | limits, newest first |
| `--json` | returns `events`, `path`, `exists`, `stats` |

## Test evidence

- `test_summary_rebuild_is_deterministic_and_leaves_raw_events_untouched`: 3 events, ids stable, raw hash unchanged after summary builds/deletes, `verify()` ok.
- `test_audit_and_memory_share_the_task_id_and_lifecycle`: raw kinds include `task.created`, `task.authorized`, `task.completed`, all with the outcome's task id.
- `test_memory.py` (pre-existing, executed): append, query by kind/task, reopen persistence, summary citation enforcement, no-replacement, corruption reporting, search.
- `aj --check` → `memory` and `memory_reader` checks green (in-memory and file-backed reopen).

## Honcho boundary

No Honcho import, config key, connection or migration exists in AJ. The memory query command reads only AJ's local SQLite file. Provider-specific memory is not present.

## Limits

- Output is newest-first; there is no ascending option.
- `--limit 0` passes 0 to the store, which SQLite treats as no rows — use a positive limit or `--limit` above the number of events.
- No full-text search exposed on the CLI (the store has `search()`, tested at the store level only).
- No export/retention command.
