# Audit Verification

## Guarantees

- Append-only JSONL, one event per line, mode 0600.
- Writer lock prevents interleaving; reader takes a shared lock.
- Key-like fields are redacted before persistence.
- Query by task, action and agent; malformed count surfaced.

## Evidence

- 4 processes × 20 writes → 80 events, 0 malformed.
- CLI: 3 events for one successful task (`task_received`, `authorized`,
  `executed`), all sharing the task id.
- Cancel/retry/recovery append `cancel_refused`, `cancel_requested`,
  `task_cancelled`, `retry_started`, `retry_refused`, `recovery_*`.
- Redaction covered by the existing health check and Phase 2 tests.

Audit bytes are unchanged by read commands and summary builds, verified directly
in `test_audit_and_raw_memory_are_append_only`.

**Result: PASS.**
