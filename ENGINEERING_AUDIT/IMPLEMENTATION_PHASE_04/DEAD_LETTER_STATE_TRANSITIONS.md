# AJ Phase 4 Batch 2: Dead-Letter State Transitions

## Overview

This document describes the dead-letter state transition behavior in AJ Phase 4 Batch 2, implementing P1-B dead-letter recovery operations.

## State Transition Graph

```
RECEIVED -> UNDERSTANDING -> PLANNED -> AUTHORIZED -> EXECUTING -> VERIFYING
                              |            |
                              v            v
                            FAILED      COMPLETED
                              |
                              v
                            RECOVERING
                           /   |    \
                          RETRY  ESCALATE ABORTED
                              |
                              v
                            DEAD_LETTER
                              |
              +-----------------+-----------------+
              |                                       |
              v                                       v
            RECOVERY_REQUIRED                     ABANDONED
              |                                       |
              v                                       v
            (manual intervention)           (deterministic terminal)
```

## Transition Rules

### 1. Dead-Leeter Operation

**When a task enters DEAD_LETTER:**

- Task transitions from FAILED (or other non-terminal state) to DEAD_LETTER
- `requires_user_decision` is set to True
- Failure is recorded in the task's error history
- Journal entry: `TASK_DEAD_LETTERED` with reason
- Audit record: `task_dead_lettered` with operation_id, capability, result="dead_letter"
- Receipt state: Agrees with task status (DEAD_LETTER)

### 2. Requeue

**Transition: DEAD_LETTER → PLANNED**

- Uses `force=True` since DEAD_LETTER is designed as a terminal state
- Preserves all historical identity (task_id, operation_id)
- Preserves all attempts (previous failed attempts remain in record.attempts)
- Creates a new execution attempt tracking entry with:
  - New attempt_id (generated via ids.new_task_id("att"))
  - New attempt_number (sequential from previous max)
  - Same operation_id (preserved from original task)
  - status: "PLANNED"
  - started_at: current time
- `requires_user_decision`: False
- Audit record: `task_requeued` with detail="requeue from dead-letter"
- Journal entry: `TASK_REQUEUED` with metadata (reason, original_status)
- Remember record: `task.requeued` preserving original_status and new_status

**Post-requeue state:**
- Task status: PLANNED
- Task is ready for re-execution
- New execution attempt is tracked but not yet started

### 3. Retry

**Transition: Creates new attempt from DEAD_LETTER state**

- Creates a new execution attempt tracking entry
- Preserves the attempt number sequence
- New attempt_id is generated
- Same operation_id is preserved
- New attempt begins from PLANNED status
- `requires_user_decision`: Depends on capability replay_safe status
- Audit record: `task_retry_started` with detail=f"retry attempt {new_attempt_number}"
- Journal entry: `TASK_RETRY_STARTED` with metadata (attempt_number, original_status)
- Remember record: `task.retry_started`

**Safety check:** If the capability is not replay-safe (`spec.retry_safe == False`):
- Retry is refused
- `requires_user_decision`: True
- Error: "capability is not declared retry-safe"
- Record: `task.retry_refused`

### 4. Abandon

**Transition: DEAD_LETTER → ABANDONED** (or any state → ABANDONED)

- Marks task status as "ABANDONED"
- `requires_user_decision`: False
- Records abandonment reason in error history
- If reason provided: `record.record_error(f"abandoned: {reason}", stage="abandonment")`
- If no reason: `record.record_error("task abandoned", stage="abandonment")`
- Saves record with reason "abandoned"
- Audit record: `task_abandoned` with detail=reason[:300]
- Journal entry: `TASK_ABANDONED` with metadata (reason)
- Remember record: `task.abandoned` with reason

**Post-abandon state:**
- Task status: ABANDONED (deterministic terminal state)
- All historical data preserved intact
- No future automatic execution
- Task remains inspectable
- Cannot be re-abandoned (raises AjError if already ABANDONED)

## Idempotency Preservation

### Inspect

- Returns complete task context without any mutation
- Exposure includes: task_id, operation_id, status, capability_id,
  attempt_histories, journal_histories, audit_continuity, lease_info,
  receipt_info, idempotency_key, errors, events, dependencies
- Critical invariant: calling inspect() multiple times returns identical
  data; no state changes occur

### Requeue

- Preserves original task identity (task_id, operation_id)
- Preserves historical attempts (previous failed attempts remain)
- Creates new execution attempt with distinct attempt_id
- Idempotency key from original task is preserved in record
- Re-execution may reuse idempotency key if same key+capability+payload

### Retry

- Creates distinct new attempt (new attempt_id, new attempt_number)
- Preserves previous failed attempts in record.attempts
- Operation identity (operation_id) remains stable
- If capability is replay-safe: new attempt may reuse idempotency key
- If capability is not replay-safe: retry is refused, no execution occurs

### Abandon

- No new execution attempt created
- All attempts preserved in record.attempts
- Operation identity remains stable
- No idempotency key reuse (task is in terminal ABANDONED state)
- Deterministic: same input always produces same terminal state

## Consistency Requirements

### Journal Consistency

- Journal remains append-only after all dead-letter recovery operations
- No historical event is deleted or rewritten
- Each operation produces exactly one journal entry
- Journal entries are: TASK_DEAD_LETTERED, TASK_REQUEUED,
  TASK_RETRY_STARTED, TASK_ABANDONED

### Receipt Consistency

- Receipt state matches actual task state after every operation
- After inspect: receipt_info.status == record.status
- After dead_letter: receipt_info.status == "DEAD_LETTER"
- After requeue: receipt_info.status == "PLANNED"
- After retry: new attempt started, receipt to be updated on completion
- After abandon: receipt_info.status == "ABANDONED"

### Audit Continuity

- Audit trail preserves lineage across all operations
- Each operation produces exactly one audit record
- Records include: task_id, operation_id, capability, result, detail
- No historical event is deleted or rewritten
- Audit records form a continuous chain from task creation through recovery

### Attempt History Consistency

- Attempt history remains complete after all operations
- Previous failed attempts are never removed
- New attempts are appended with distinct attempt_ids
- Attempt numbering is sequential and consistent
- Failed attempt details (failure, ended_at) preserved

## Concurrency Safety

### Inspect Concurrent Access

- Multiple processes can inspect the same DEAD_LETTER task safely
- No mutation occurs during inspection
- SQLite WAL mode ensures read consistency
- Outcome: all inspectors observe identical state; no corruption

### Requeue Concurrent Access

- Two processes attempting requeue simultaneously:
  - First process wins: transitions DEAD_LETTER → PLANNED, creates attempt
  - Second process: fails with AjError "task is not in DEAD_LETTER state"
  - Outcome: deterministic; only one requeue succeeds
- Locking: SQLite exclusive lock during transition

### Retry Concurrent Access

- Two processes attempting retry simultaneously:
  - First process wins: creates new attempt, transitions toward execution
  - Second process: AjError if task no longer in DEAD_LETTER, or creates
    separate attempt if architecture permits (tested behavior)
- Outcome: correct locking/state transition; no duplicate execution caused
  by race due to SQLite WAL coordination

### Abandon Concurrent Access

- Two processes attempting abandon simultaneously:
  - First process wins: transitions to ABANDONED, records in journal/audit
  - Second process: AjError "task is already abandoned"
- Outcome: one deterministic terminal transition wins; losing operation
  fails safely with well-defined error

## Dependency Safety

### Requeue with Satisfied Dependencies

- Task transitions DEAD_LETTER → PLANNED
- Dependencies are re-evaluated in new PLANNED state
- If all dependencies satisfied: task proceeds to AUTHORIZED → EXECUTING
- If some dependencies unsatisfied: task remains in PLANNED until resolved

### Requeue with Unsatisfied Dependencies

- Task transitions DEAD_LETTER → PLANNED
- Dependencies remain unsatisfied
- Task stays in PLANNED state (not AUTOMATICALLY executed)
- Requires manual or external resolution before execution
- Prevents dead-letter task from bypassing dependency enforcement

### Retry with Dependencies

- New attempt begins from PLANNED state
- Dependency check performed before execution
- If dependencies unsatisfied: execution blocked, task remains PLANNED
- Safety mechanism prevents dead-letter task from bypassing dependency checks

## Lease Safety

### No Active Lease

- Dead-letter task has no active lease
- All operations (inspect, requeue, retry, abandon) proceed normally
- No risk of stealing or duplicating active execution

### Expired Lease

- If lease has expired: safe to proceed with all operations
- Lease expiry is detected via leases.is_active() returning False

### Active Operation Lease

- If task has active operation lease: requeue and retry are blocked
- Inspect and abandon proceed normally
- Outcome: prevents stealing in-progress execution; P1-C will harden further

### Stale Worker Scenario

- Stale worker scenario: lease may be stale but not actively holding
- Inspect always safe; other operations depend on leases.is_active() result
- P1-C will add further lease/crash hardening

## Limitations and Workarounds

### DEAD_LETTER is Terminal

- DEAD_LETTER is designed as a terminal state per existing architecture
- Requeue uses force=True to bypass this, which is intentional
- Workaround: use requeue for recovery, accept terminal semantics

### No Distributed Coordination

- AJ remains single-machine; no distributed locks or consensus protocols
- Concurrency safety relies on SQLite WAL/locking only
- P1-C will later harden crash behavior further

### Exact-once External Effects

- AJ cannot guarantee exactly-once execution of external effects
- Idempotent replay only works for internal capabilities
- Dead-letter recovery operates on internal logical operations

### Failure of Requeue After Multiple Dead-Leeter Cycles

- If a task is dead-lettered, requeued, fails again, and dead-lettered
  again: each cycle preserves full history
- Requeue always possible from DEAD_LETTER state
- No limit on requeue cycles (architecture allows repeated recovery)

## Test Coverage

The following behavioral aspects are verified:

1. State transition correctness (DEAD_LETTER → PLANNED → ...)
2. History preservation (attempts, journal, audit not erased)
3. Idempotency (same key + same capability + same payload → replay)
4. Conflict detection (same key + different capability/payload → conflict)
5. Safety policy (non-replay-safe → recovery_required, not auto-replay)
6. Concurrent access (deterministic outcomes)
7. Dependency enforcement (blocked if unsatisfied)
8. Lease safety (no active lease required for operations)
9. Idempotency of abandon (idempotent terminal state)
10. Receipt/journal/audit consistency after each operation

## Files Modified

- `AJ/aj/orchestrator.py` — Added inspect, dead_letter, requeue, retry, abandon methods

## Files Created

- `ENGINEERING_AUDIT/IMPLEMENTATION_PHASE_04/DEAD_LETTER_STATE_TRANSITIONS.md`