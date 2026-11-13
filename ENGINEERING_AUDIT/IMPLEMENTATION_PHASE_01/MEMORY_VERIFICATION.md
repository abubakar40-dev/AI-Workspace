# Memory Verification

## What was wired

`Aj` accepts an injected `MemoryStore`. On every accepted request it appends canonical raw events:

| Event kind | When | Metadata |
|---|---|---|
| `task.created` | task record created | `owner_agent` |
| `task.authorized` | policy returned ALLOW | `capability`, `permission_level` |
| `task.completed` | internal, Hermes or agent path completed | `capability`/`agent`, `status` |
| `task.failed` | routing/policy/execution failure | `agent`, `capability`, `code`, `stage`, `status` |
| `task.cancelled` | operator cancel | `status` |

A memory write failure never breaks a task: it is recorded on the task as a warning, and the returned id is `None`.

## Verified persistence (demo)

Command: `python -m aj --demo`

| Item | Value |
|---|---|
| Store | `~/.local/share/aj/memory.sqlite3` (SQLite) |
| Raw events | 3, ids `1,2,3` |
| Task id | `aj_20261110T093254_9c099430` (same on all three events) |
| Kinds | `task.created`, `task.authorized`, `task.completed` |
| Source | `aj` |
| Summaries | 0 (none created by the runtime) |

Independent query of the same SQLite file returned the same three rows with matching `task_id` and `source`, so the records survive process exit.

Task records are separately persisted to `~/.local/share/aj/tasks.jsonl`, one JSON object per change, with the full transition list.

## Verified guarantees (tests)

From `tests/test_memory.py` (pre-existing, now executed):

1. **Append** returns increasing ids; `events()` is queryable by kind and task id.
2. **Retrieval** returns the original content.
3. **Multiple writes** survive and counts are exact.
4. **Stable ids** persist across reopening the database.
5. **Provenance** (`source`, `task_id`, `meta`, `at`) survives.
6. **Raw is never replaced**: adding a summary leaves `count_events()` unchanged and `source_events()` still returns the original words.
7. **Citations are enforced**: a summary with no sources or with non-existent ids is rejected.
8. **Corruption is visible**: after simulated external deletion, `verify()` reports the broken citation instead of silently passing.
9. **Search** spans raw events and summaries; blank queries return nothing.

## Contract compliance

| Rule | Status |
|---|---|
| Raw records canonical, append-only | Yes — no delete API in `MemoryStore` |
| Summaries derived, cite raw ids | Yes — enforced at insert |
| Honcho optional adapter, absent here | Yes — no import, call or config dependency |
| No migration of existing Honcho data | Yes — nothing migrated or read |
| No secrets in memory | Runtime writes task metadata only; no payload echo, no token |

## Not verified

- Retention/compaction policy (none implemented).
- Concurrent writers across processes (SQLite + a per-instance RLock only; single process assumed).
- Query-by-time/actor CLI (store supports `since`, kind and task id; no CLI yet).
