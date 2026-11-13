# Known Issues — Phase 02

## Functional gaps

1. **No cancel/retry CLI.** `Aj.cancel()`/`Aj.retry()` exist and are tested, but `aj cancel`/`aj retry` are not exposed; adding them needs a decision on status precedence.
2. **No summary CLI.** Summaries are built and verified by tests and the health check only.
3. **`aj recover` uses the persisted payload.** Tasks created before Phase 2 have `request_payload = {}`; a replay-safe older task would replay with an empty payload.
4. **Recovery ignores `max_attempts`.** It is an explicit human action, so no bound is enforced; a caller could replay a task that failed repeatedly.
5. **No startup recovery.** `aj recover` must be run explicitly. Deliberate, but worth stating.

## Persistence/concurrency

6. **No cross-process lock.** Two writers appending to `tasks.jsonl` concurrently could interleave; single-user foreground use is assumed.
7. **No compaction/retention.** `tasks.jsonl` appends a full record per change and grows monotonically.
8. **Task reload is last-record-wins.** A record truncated by a crash mid-write is reported as malformed; the previous complete line remains authoritative only if the truncated line is later in the file and skipped — recovery then reflects the last valid record, which may be slightly stale.
9. **`tasks`/`task` read from `core.data_dir` regardless of `persist_tasks`.** Read-only and harmless, but the flag does not gate inspection.

## CLI/behaviour notes

10. **`aj.delegate` is declared but not internal.** Its adapter is `aj.orchestrator`, so `aj run --capability aj.delegate` is refused as non-internal. That is correct for Phase 2, but the declaration may read as runnable; it delegates only through the orchestrator API.
11. **Memory output is newest-first** and `--limit 0` yields no rows (SQLite limit 0).
12. **Health `imports` count changed** from 20 to 23 modules (summary, recovery, new CLI dependencies), so the detail number in older reports is stale.
13. **Audit `read_events` reads whole files** before applying `limit`; fine at current scale, not streaming.

## Verification gaps

14. **Python 3.14.4 only.** `requires-python >=3.10` is declared but 3.10–3.13 were not run.
15. **No linter/type checker/coverage tool.** None installed.
16. **No git repository.** No diff, history or baseline commit exists for AJ.
17. **Recovery tested with internal actions only**, by design. External replay is unimplemented, not merely untested.
