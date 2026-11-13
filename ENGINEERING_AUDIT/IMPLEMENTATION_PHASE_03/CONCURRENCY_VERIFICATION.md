# Concurrency Verification

## Mechanism

- `aj/locking.py` uses `fcntl.flock` on sidecar `*.lock` files, non-blocking with
  a bounded poll and timeout (`StorageBusy`).
- Writers serialise; readers take shared locks; locks release on exception and
  process exit (no stale-lock heuristic needed).
- Task and audit appends use lock + append + flush.
- SQLite uses WAL and a 30 s busy timeout.

## Tests (real OS processes, `fork`)

| Store | Writers | Writes each | Expected | Observed |
|---|---|---|---|---|
| `tasks.jsonl` | 4 | 15 | 60 valid lines | 60 lines, 60 tasks, 0 malformed |
| audit JSONL | 4 | 20 | 80 events | 80 events, 0 malformed |
| memory SQLite | 4 | 20 | 80 events | 80 events, 80 unique ids |

Additional test: a second lock acquisition times out with `StorageBusy`, and an
exception inside the lock still releases it.

## Caveat

Locks are advisory and POSIX-only. Windows fallback is a documented no-op. A
process that ignores the lock can still write directly to the files.

**Result: PASS.**
