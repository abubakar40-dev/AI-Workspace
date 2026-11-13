# Summary Rebuild Verification — Phase 02

## Implementation

`aj/summary.py` computes a digest directly from canonical raw events:

| Field | Meaning |
|---|---|
| `event_count` | number of raw events |
| `task_count` | distinct task ids |
| `by_kind` | count per event kind, sorted |
| `tasks` | per task: event count, last kind, last status, capability |
| `capabilities` | sorted set of capabilities seen in metadata |
| `first_event_id`, `last_event_id` | id range |

Content is canonical JSON (`sort_keys=True`, compact separators), so the same events always produce the same bytes. `build()` stores it as a summary with `source_event_ids` equal to **every** contributing raw id.

There is no model, provider, clock or randomness in the computation.

## Verified

From `test_summary_rebuild_is_deterministic_and_leaves_raw_events_untouched`:

| Check | Result |
|---|---|
| Build twice from identical events | `content` identical; `source_event_ids` identical |
| Digest values | `task_count == 1`, `by_kind["task.completed"] == 1` |
| Raw events before vs after | SHA-256 of canonical event JSON unchanged |
| Raw count | still 3 |
| Delete summary A and B | `delete()` returns `True` for both; `summaries(kind="task_digest") == []` |
| Rebuild after deletion | content equals the first build exactly |
| Citations valid | `verify()["ok"] is True` after rebuild |
| Raw history | unchanged by deletion and rebuild |

`aj --check` → `summary` check builds a digest twice from two synthetic events, requires identical content, `verify()` ok and exactly 2 raw events.

## Invariant

```
raw_before == raw_after
```

is asserted by comparing a hash of the full serialised raw-event list, not just counts.

## Limits

- No summary CLI (`aj summary build|list`) yet; summaries are exercised by tests and the health check.
- The digest includes event content, so appending any raw event changes the rebuild — that is correct for a canonical ledger, but means summaries are snapshots, not incremental caches.
- `summary.delete()` uses the store's internal connection because there is intentionally no public summary-deletion API; it removes only `summaries` rows.
- No adapter consumes summaries yet (no Honcho, no embeddings).
