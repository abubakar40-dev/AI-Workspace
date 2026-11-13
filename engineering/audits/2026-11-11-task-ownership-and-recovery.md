# Task Ownership, Lease, Cancellation, and Recovery (evidence-based, 2026-11-11)

Sources: `AJ/aj/lease.py`, `aj/orchestrator.py` (`leases.hold`, retry/recover/cancel/resume), `aj/scheduler.py`, `aj/task.py`, `aj/receipts.py`, `aj/idempotency.py`, `aj/journal.py`, tests `tests/test_crash_safety.py`, `tests/test_phase3.py`, `tests/test_f2_*`.

## Lease acquisition, renewal, expiry, reacquisition, ownership
- **Operations:** `LeaseManager` supports operation leases (`cancel/retry/recover`) and execution leases (`execute`). Acquire checks active/expired leases per task, prevents conflicting active operations, and binds worker/pid/host/timestamps (`lease.py`).
- **Execution lease semantics:** expired execution lease raises `LeaseExpired` and does **not** authorize mutation (per implementation/comments); same worker can renew heartbeat; different worker cannot usurp valid lease. `hold()` context acquires and auto-releases by operation type.
- **Scheduler ownership:** scheduler acquires execution lease with worker id, runs task via `resume(task_id, leased=True)` (fixed this segment to avoid nested acquire/release issues), releases in finally.
- **VERIFIED (existing tests):** crash-safety suite covers lease expiry/reacquisition/ownership conflict and recovery assessment behaviors in key scenarios (14 tests total). `aj --check` reports lease status.
- **VERIFICATION REQUIRED:** exhaustive competing-worker/deterministic race proofs for every mutating path, stale-worker kill/interruption at exact ownership-change boundaries, and long-running heartbeat behavior under real process interruption.

## Cancellation semantics
- **VERIFIED by existing behavior/API shape (partial):** cancellation is mediated through task state/lease/orchestrator paths (not a blind force-kill of in-flight external side effects). Tasks record errors/decisions and terminal states where allowed.
- **NOT FULLY VERIFIED:** cooperative vs immediate cancellation during queued/active/retry-waiting/recovery/side-effect initiation vs completion; whether any in-flight external side effect can outlive a reported cancellation.
- **Honest guarantee:** cancellation must not be reported as successful if the side effect may already have occurred. Current implementation provides state/request semantics in covered paths but **does not prove universal safe interruption of in-flight side effects** — **VERIFICATION REQUIRED** (and may require explicit cancellation-requested semantics for in-flight operations).

## Idempotency and receipts interaction
- **Mechanisms present:** `aj/idempotency.py` (`IdempotencyStore`), `aj/receipts.py` (`ReceiptStore`), journal events, task `idempotency_key`/operation/attempt metadata, and replay/retry-safe gating in orchestrator/recovery.
- **VERIFIED (existing):** idempotency conflict/replay and receipt/journal persistence are exercised in crash-safety/phase tests and normal execution flows; recovery refuses unsafe replay for non-replay-safe/internal cases per policy.
- **Guarantee (honest):** recovery/retry aims to avoid repeating already-committed side effects where adapter/action contracts and recorded receipts/idempotency evidence support it. **Universal exactly-once execution is NOT claimed** (external side effects may be at-most-once/at-least-once depending on adapter/commit point).
- **VERIFICATION REQUIRED:** proof for every side-effecting adapter path (including Hermes/external/calling), and deterministic interruption between side-effect commit and durable receipt/state commit for each production boundary.

## Recovery behavior
- **VERIFIED/PARTIAL:** retry requires `retry_safe` and now re-authorizes at boundary (F2 hardening). Recovery requires replay-safe/internal capability conditions and now re-authorizes; refuses unsafe replay and moves to recovery/dead-letter/manual-decision paths as appropriate. Dead-letter path records audit/journal/memory evidence.
- **VERIFICATION REQUIRED:** complete per-boundary recovery classification evidence for all 1–16/A–F crash points (bounded; see crash matrix update).
