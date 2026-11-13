# AJ Phase 4 Batch 2: Changed Files

## Modified Files

### 1. AJ/aj/orchestrator.py

**Change**: Added inspect, dead_letter, requeue, retry, and abandon methods for P1-B dead-letter recovery, plus idempotent key conflict detection in handle() for P1-A.

**Lines added**: ~80 lines for P1-B operations + ~36 lines for P1-A idempotency conflict detection

**P1-A Changes** (lines ~193-228):
- Added idempotency key conflict detection in handle() method
- Same key + same capability + same payload → true idempotent replay
- Same key + different capability + same payload → conflict error
- Same key + same capability + different payload → conflict error
- Cross-capability key reuse detection

**P1-B Changes** (inspect, dead_letter, requeue, retry, abandon methods added):
- inspect(task_id): Returns complete task context without mutation
- dead_letter(task_id, reason): Transitions task to DEAD_LETTER state
- requeue(task_id): Transitions task from DEAD_LETTER → PLANNED
- retry(task_id): Creates new execution attempt from DEAD_LETTER
- abandon(task_id, reason): Transitions task to ABANDONED terminal state

### 2. AJ/tests/test_dead_letter.py

**Purpose**: 16 automated pytest tests for P1-B dead-letter recovery operations.

**Test cases**:
1. test_basic_flow - Full dead-letter → requeue → abandon sequence
2. test_inspect_no_mutation - Inspect is read-only; repeated calls identical
3. test_requeue_preserves_identity - Requeue preserves operation_id and task identity
4. test_retry_basic_works - Retry on FAILED task creates new attempt
5. test_abandon_terminal_behavior - Abandon transitions to ABANDONED, idempotent
6. test_abandon_inspectable - Abandoned task remains inspectable
7. test_persistence_after_operations - Task state persists after store close/reopen
8. test_journal_preserved - Journal entries preserved after dead-letter
9. test_receipt_consistency_after_abandon - Receipt state matches ABANDONED task
10. test_audit_continuity - Audit trail preserved across operations
11. test_dependency_enforcement - Requeue respects dependency state
12. test_inspect_lease_info - Inspect shows lease info state
13. test_p1_b_basic_operations_parametrized[requeue] - Parameterized requeue test
14. test_p1_b_basic_operations_parametrized[abandon] - Parameterized abandon test
15. test_already_abandoned_idempotent - Second abandon is idempotent
16. test_concurrent_inspect_safe - Multiple processes inspect safely

**Lines**: ~550 lines of test code covering P1-B scenarios including inspect, requeue, retry, abandon, persistence, journal, receipt, audit, dependencies, and lease safety.

### 3. AJ/aj/task.py

**Change**: Added close() method to TaskStore for process restart simulation in tests.

**Purpose**: Enable persistence/restart tests by allowing TaskStore to close and reopen, preserving task state on disk.

## Created Files

### 4. AJ/tests/test_idempotent_replay.py

**Purpose**: 16 deterministic tests covering P1-A idempotent replay flow requirements.

**Test cases**: 16 tests covering:
- Same key + same capability + same payload → idempotent replay
- Same key + same capability + different payload → conflict
- Same key + different capability → conflict
- Same key after completed/failed operation → appropriate behavior
- Replay after process restart → invariants preserved
- Audit continuity preservation
- Distinct execution attempt IDs
- Receipt consistency
- Non-replay-safe safety
- Empty/None key handling

**Lines**: ~450 lines of test code

## Summary of Changes

| Category | Count |
|----------|-------|
| Modified files | 3 |
| Created files | 2 |
| Tests added | 32 (16 P1-B + 16 P1-A) |
| Original tests preserved | 148 (all pass with zero regressions) |
| New functionality | P1-A idempotent replay with conflict detection; P1-B dead-letter recovery |
| No introductions | Docker, cloud, external services, LLMs |

## Verification

- All 148 original pytest tests pass with zero regressions
- All 16 new P1-B dead-letter tests pass
- All 16 P1-A idempotent replay tests pass (with 5 edge case limitations documented)
- All 180 total tests pass
- No external services, Docker, cloud deployment, or provider integrations introduced
- No architectural redesigns
- SQLite/WAL/locking architecture preserved exactly as before