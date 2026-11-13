# AJ Phase 4 Batch 2: P1-B Known Limitations

## Overview

This document outlines the known limitations of the P1-B dead-letter recovery implementation. Each limitation is documented with its current behavior, impact, and any planned future work (P1-C or later).

## Limitations

### 1. DEAD_LETTER is Terminal by Design

**Limitation**: DEAD_LETTER state is designed as a terminal state in the existing architecture.

**Behavior**: 
- Task transitions to DEAD_LETTER with requires_user_decision = True
- Requeue uses force=True to bypass terminal state semantics
- This is an intentional architectural decision, not a bug

**Impact**: 
- Recovery from DEAD_LETTER requires explicit administrative operations (requeue, retry, abandon)
- Automatic recovery not possible; requires manual intervention
- Forceful bypass of terminal state may have unintended consequences in edge cases

**Workaround**: 
- Use requeue() for recovery when needed
- Accept that DEAD_LETTER is meant to signal permanent failure
- P1-C will explore whether DEAD_LETTER terminal semantics should be relaxed

### 2. No Distributed Coordination

**Limitation**: AJ remains single-machine; no distributed locks or consensus protocols.

**Behavior**: 
- Concurrency safety relies on SQLite WAL/locking only
- No multi-machine coordination for dead-letter recovery
- Concurrent processes on same database may experience SQLite locking errors

**Impact**: 
- Single point of failure for recovery operations
- Only one process can modify a task at a time (SQLite serializes writes)
- Cross-machine recovery not supported

**Workaround**: 
- Serialize recovery operations through a single coordinator
- P1-C will add crash recovery within single machine only

### 3. Exact-once External Effects Not Guaranteed

**Limitation**: AJ cannot guarantee exactly-once execution of external effects.

**Behavior**: 
- Idempotent replay only works for internal capabilities
- External API calls, side effects not covered by idempotency
- Dead-letter recovery operates on internal logical operations only

**Impact**: 
- Retrying a task with external effects may cause duplicate external actions
- Requeuing may trigger external systems again
- Idempotency key only meaningful for internal capability replay

**Workaround**: 
- Ensure capabilities are declared replay-safe (retry_safe=True)
- External systems should be idempotent-capable
- P1-C will add external effect tracking (deferred)

### 4. DEAD_LETTER State Not Idempotent Across Cycles

**Limitation**: Repeated dead-letter/requeue cycles accumulate metadata but don't reset.

**Behavior**: 
- Each dead-letter cycle records new error entries
- Each requeue preserves all historical attempts
- Each abandon preserves all attempts indefinitely
- No automatic cleanup or compression of history

**Impact**: 
- Task records may grow in size over many cycles
- Error history becomes increasingly verbose
- No automatic pruning of old failure records

**Workaround**: 
- Manual cleanup via database operations if needed
- P1-C may add history management (deferred)

### 5. No Automatic Dependency Resolution After Requeue

**Limitation**: After requeue from DEAD_LETTER → PLANNED, dependencies are re-evaluated but not automatically resolved.

**Behavior**: 
- Task stays in PLANNED state if dependencies unsatisfied
- No automatic dependency resolution or task generation
- Manual or external resolution required

**Impact**: 
- Dead-letter task with unsatisfied dependencies remains in PLANNED
- Cannot proceed to execution until dependencies satisfied
- May require external intervention to satisfy dependencies

**Workaround**: 
- Satisfy dependencies externally before re-execution
- P1-C will add automatic dependency resolution (deferred)

### 6. Lease Safety Basic, Not Hardened

**Limitation**: P1-B basic lease checking; P1-C will harden further.

**Behavior**: 
- No active lease: all operations proceed
- Expired lease: operations proceed (is_active returns False)
- Active operation lease: requeue/retry blocked, inspect/abandon allowed
- Stale worker: behavior depends on lease implementation

**Impact**: 
- P1-B does not fully prevent lease-related issues
- Active execution may be stolen if lease logic incomplete
- P1-C will add: lease expiry, crash-hardened leases, stale worker detection

**Workaround**: 
- Ensure lease system is properly configured before P1-C
- P1-C will harden lease/crash behavior further (per roadmap)

### 7. No Test Coverage via pytest Functions

**Limitation**: All P1-B behavior verified via manual scripts, not formal pytest test functions.

**Behavior**: 
- 0 new test functions added to tests/ directory
- Verification done through dedicated Python scripts
- Existing 148-test suite continues to pass

**Impact**: 
- No pytest-driven test suite for P1-B behavior
- Manual verification may miss edge cases
- Future work: add pytest test functions for P1-B

**Workaround**: 
- P1-C will include comprehensive pytest test creation
- For now, manual scripts provide verification

### 8. Retry Safety Dependent on Capability Declaration

**Limitation**: Retry from dead-letter respects capability.retry_safe flag.

**Behavior**: 
- If spec.retry_safe == False: retry refused, recovery_required
- If spec.retry_safe == True: new attempt created, may proceed
- Declaration must be set correctly in capability specs

**Impact**: 
- Some capabilities may not support retry from dead-letter
- User must ensure capability.retry_safe is correctly set
- Mis-declaration may cause unexpected refusals or unsafe replays

**Workaround**: 
- Review capability specs for retry_safe flag
- P1-C will add default values and validation (deferred)

### 9. Abandon Does Not Signal External Systems

**Limitation**: Abandon produces deterministic terminal state but does not notify external systems.

**Behavior**: 
- Task status changes to ABANDONED
- Journal entry: TASK_ABANDONED
- Audit record: task_abandoned
- No external signaling or webhook triggers

**Impact**: 
- External systems unaware of abandonment
- May continue to expect task completion or retry
- User must implement external signaling separately if needed

**Workaround**: 
- Implement external notification in application logic
- P1-C may add external event publishing (deferred)

### 10. Inspect Does Not Expose Full Lease Details

**Limitation**: Inspect returns lease_info summary, not full lease object.

**Behavior**: 
- lease_info includes: is_active, expiry_time, lease_type
- Full lease object (holders, renewal info, etc.) not exposed
- May limit diagnostic capability for lease-related issues

**Impact**: 
- Limited visibility into active lease details during inspection
- May miss stale lease identification

**Workaround**: 
- Access lease store directly for detailed lease inspection
- P1-C will expand inspect lease fields (deferred)

## Interaction with P1-A Idempotency

### P1-A Invariants Preserved

| Invariant | Status |
|---|---|
| Stable operation identity | ✅ Preserved |
| Distinct execution attempts | ✅ Preserved |
| No duplicate successful result | ✅ Preserved |
| Safe incomplete operation | ✅ Preserved |
| Audit continuity | ✅ Preserved |
| Receipt consistency | ✅ Preserved |
| Journal consistency | ✅ Preserved |

### P1-A Conflicts with P1-B

| Conflict | Resolution |
|---|---|
| Same key + same capability + same payload → idempotent replay | ✅ Preserved; requeue/retry/abandon operate on existing logical operation |
| Same key + different capability + same payload → conflict error | ✅ Preserved; cross-capability detection unchanged |
| Non-replay-safe capabilities → recovery_required | ✅ Preserved; dead-letter recovery respects safety policy |

### P1-B New Behavioral Invariants

| New Invariant | Description |
|---|---|
| inspect() idempotent | Multiple calls return identical data; no mutation |
| requeue from DEAD_LETTER uses force=True | Bypasses terminal state per architectural decision |
| abandon() idempotent terminal | Second call from ABANDONED raises AjError |
| history preservation across recovery | All attempts, journal, audit preserved through recovery cycle |
| operation identity stable | operation_id unchanged across dead-letter/requeue/retry/abandon cycles |

## Interaction with P1-C (Future)

### P1-C Will Address

| Limitation | P1-C Planned Action |
|---|---|
| DEAD_LETTER terminal semantics | Explore non-terminal redesign |
| No distributed coordination | May add optional distributed locks |
| Exact-once external effects | Add external effect tracking |
| History accumulation | Add history management/pruning |
| Dependency auto-resolution | Add automatic dependency resolution |
| Lease safety hardening | Add lease expiry, crash-hardened leases, stale worker detection |
| pytest test coverage | Comprehensive P1-B and P1-C test suites |
| Retry safety defaults | Add default retry_safe values, validation |
| External system signaling | Add external event publishing on abandon |
| Inspect lease details | Expand inspect output with full lease info |

## Deferred and Out of Scope

The following are explicitly deferred or out of scope for P1-B:

- Docker or cloud infrastructure integration
- Distributed coordination or consensus protocols
- External API exactly-once guarantees
- LLM or local AI infrastructure
- Architectural redesign of AJ
- Replacement of SQLite/WAL
- Deletion of historical task data
- Weakening idempotency guarantees (P1-A)
- Claims of exactly-once external effects
- Bypass of dependency checks
- Bypass of lease checks
- Silent auto-replay of unsafe operations

## Files Reference

- Modified: `AJ/aj/orchestrator.py`
- Modified: `AJ/aj/task.py` (close method only)
- Created: `ENGINEERING_AUDIT/IMPLEMENTATION_PHASE_04/KNOWN_LIMITATIONS_P1_B.md`
- Related: `ENGINEERING_AUDIT/IMPLEMENTATION_PHASE_04/BATCH_2_IMPLEMENTATION_REPORT.md`