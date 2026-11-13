# Known Issues and Deliberate Limitations

1. **POSIX locking only.** `fcntl.flock` is Linux/Unix. On platforms without it,
   `file_lock` is a no-op and reports `available() == False`. No portable
   cross-platform lock was added.
2. **Append logs are not fsynced.** Task/audit appends use lock + flush. They
   survive process crashes and concurrent writers, but an OS/power failure can
   lose the last lines. Export and backup do fsync + atomic replace.
3. **Cooperative cancellation.** `CANCEL_REQUESTED` is honest but cannot stop a
   hypothetical running process. Persisted `EXECUTING` implies a crashed or
   external worker; AJ does not pretend to kill it.
4. **Retry is limited to declared capabilities.** Only `aj.echo` and
   `aj.health_check` are `retry_safe`. External actions cannot retry until a
   capability explicitly declares it.
5. **Import does not preserve memory event ids.** Content, timestamps, source,
   task correlation and provenance are preserved; ids are reassigned and
   summaries rebuilt. Task ids are preserved and conflicts refused.
6. **Import requires disjoint task ids.** Merging two divergent versions of the
   same task is refused rather than guessed.
7. **Configuration origins are section-level**, not per-key. This is enough for
   operator diagnosis but not a full provenance system.
8. **Redaction is key-based.** Free-text secrets are not detected. Exports and
   backups are plaintext.
9. **No cross-process task mutation guard.** Appends are safe, but two operators
   can still issue conflicting cancel/retry commands; the state machine rejects
   illegal transitions and the last valid append wins.
10. **Lock timeouts are 5 s.** A stalled writer causes `storage_busy` (exit 5)
    rather than waiting indefinitely.
11. **No retention/compaction.** JSONL grows with every transition; no pruning.
12. **Health checks use temporary stores**, so they verify mechanisms, not the
    operator's actual dataset; `aj diagnostics` is the read-only view of real
    state.
