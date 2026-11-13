# Performance Sanity

Not a benchmark; a local check that the store and locks do not collapse under a
small operator workload.

```text
120 tasks in 0.34s
1 passed, 117 deselected in 0.53s
```

- Workload: 120 `aj.echo` tasks, each with full transitions, attempts, audit and
  raw memory, using the standard locked stores in a pytest temporary directory.
- After the run: 120 task records, 0 malformed, ≥120 audit events, ≥120 raw
  events, all successful.
- No external provider, network or large dataset involved.

Observed write behavior is dominated by per-transition appends; no premature
optimization was applied. Queries remain simple scans over JSONL and indexed
SQLite rows.

**Result: PASS.**
