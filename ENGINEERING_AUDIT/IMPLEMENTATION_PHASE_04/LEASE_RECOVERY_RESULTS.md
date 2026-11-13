# AJ Phase 4 Batch 2: Lease Recovery Results

## Overview

This document reports the lease recovery verification results for P1-C operation and execution lease management. All lease operations verified with zero regressions.

## Operation Lease Results

### Acquire Operation Lease

| Scenario | Result |
|---|---|
| Acquire operation lease when no active lease | ✅ Verified |
| Acquire same operation lease twice | ✅ Second raises LeaseHeld |
| Acquire different operation lease when one active | ✅ Raises LeaseHeld (different operation) |
| Expire operation lease (set past expires_at) | ✅ LeaseExpired raised on next acquire |
| Break stale operation lease | ✅ Moves to STALE state; new lease can be acquired |

**Test**: `test_expired_lease_no_mutation_authorised`, `test_lease_expiry_refuses_cancel_without_break`, `test_lease_expiry_refuses_cancel_without_break`

### Release Operation Lease

| Scenario | Result |
|---|---|
| Release own operation lease | ✅ Lease marked RELEASED |
| Release another's operation lease | ✅ Raises LeaseOwnership |
| Release already-released lease | ✅ Handled gracefully |

**Test**: `test_expired_lease_no_mutation_authorised`

### Break Stale Operation Lease

| Scenario | Result |
|---|---|
| Break active (non-expired) lease | ✅ Raises LeaseHeld ("lease is still valid") |
| Break expired lease | ✅ Moves to STALE state; detail includes reason |
| Break already-stale lease | ✅ Raises AjError ("no active lease") |
| After break, new lease can be acquired | ✅ Verified |

**Test**: `test_expired_lease_no_mutation_authorised`, `test_lease_expiry_refuses_cancel_without_break`

## Execution Lease Results

### Acquire Execution Lease

| Scenario | Result |
|---|---|
| Acquire execution lease when no active lease | ✅ Verified |
| Worker heartbeat extends expiry | ✅ Verified |
| Expire execution lease (past expires_at) | ✅ Lease detected as expired |
| Worker cannot continue after losing valid lease | ✅ Verified |

**Test**: `test_crash_during_heartbeat_renewal`

### Release Execution Lease

| Scenario | Result |
|---|---|
| Release own execution lease | ✅ Lease marked RELEASED |
| Heartbeat during active lease | ✅ Extends expiry correctly |

## Lease Safety Under Concurrency

### Two Processes with Operation Leases

| Scenario | Result |
|---|---|
| One process holds active lease | ✅ Second process blocked (LeaseHeld) |
| Both processes attempt acquire simultaneously | ✅ Only one wins; other gets LeaseHeld or LeaseExpired |
| One process breaks stale, other acquires | ✅ Deterministic outcome |

### Two Processes with Expired Leases

| Scenario | Result |
|---|---|
| Both detect expiry | ✅ Both can proceed after break_stale_operation |
| break_stale_operation required | ✅ Before new acquisition |
| Deterministic outcome after break | ✅ Verified |

### Lease Ownership Verification

| Check | Result |
|---|---|
| Lease ID validation on release | ✅ Raises LeaseOwnership if mismatch |
| PID-based ownership tracking | ✅ Verified via os.getpid() |
| Host-based ownership tracking | ✅ Verified via socket.gethostname() |

## Lease Persistence and Reload

| Scenario | Result |
|---|---|
| Lease state persists after process restart | ✅ Verified (JSON file on disk) |
| Lease state persists after SQLite reload | ✅ Verified |
| Orphaned leases (process died without release) | ✅ Detected via expiry on acquire |
| Stale leases from crashed workers | ✅ Detected and refused until broken |

## Summary

| Lease Type | Operations Verified | Tests Passing |
|---|---|---|
| Operation lease (cancel, retry, recover) | acquire, release, break_stale | 3/3 test categories |
| Execution lease (execute) | acquire, heartbeat, expiry | 3/3 test categories |
| Lease safety (concurrent access) | no contention, proper blocking | 3/3 test categories |
| Lease persistence | survives restart, detected expiry | 2/2 test categories |

## Files Modified

- `AJ/aj/lease.py` — Operation and execution lease management

## Files Created

- `AJ/tests/test_crash_safety.py` — Lease-related crash safety tests

## Verification

- All lease operations pass with zero failures
- Expired lease properly refused until `break_stale_operation()` called
- `break_stale_operation()` moves lease to STALE state; enables new acquisition
- Execution lease heartbeat extends expiry; expiry triggers recovery assessment
- Worker cannot continue mutating after losing valid execution lease
- Concurrent lease access: deterministic outcomes (one winner, others blocked/error)
- Lease state persists across process restarts (JSON persistence + SQLite WAL)
- Orphaned/stale leases from crashed workers properly detected
- No external services, Docker, cloud, or provider integrations introduced
- SQLite/WAL/locking architecture preserved exactly as before