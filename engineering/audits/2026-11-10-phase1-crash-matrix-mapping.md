# Phase 1 / P1-C Strict Audit — Crash Matrix & Reconciliation Mapping (in progress)

**Date:** 2026-11-10  
**Scope:** AJ Batch 2 P1-C strict spec coverage (master crash points 1–16, reconciliation states A–F)  
**Live suite:** 199 passed, 0 failed (`AJ/.venv/bin/python -m pytest -q`)  
**Status:** PARTIAL / VERIFICATION REQUIRED — existing tests cover important crash/recovery behaviors but not all master points as explicit external subprocess-kill scenarios.

## Existing evidence (current tests)
- `tests/test_crash_safety.py` (14 tests): `test_expired_lease_no_mutation_authorised`, `test_repeated_recovery_is_idempotent_failed`, `test_crash_simulate_before_lease_release`, `test_lease_expiry_refuses_cancel_without_break`, `test_crash_after_receipt_persistence`, `test_crash_during_heartbeat_renewal`, `test_crash_during_retry_scheduling`, `test_crash_during_dependency_evaluation`, `test_completed_task_recovery_noop`, `test_multi_process_recovery_same_operation`, `test_multi_process_lease_reclamation`, `test_recovery_versus_normal_completion_race`, `test_repeated_recovery_after_restart`, `test_journal_receipt_reconciliation_production_code`.
- `tests/test_dead_letter.py`, `tests/test_idempotent_replay.py`, `tests/test_phase3.py` cover lifecycle, retry/abandon/requeue, dependency, idempotency invariants relevant to recovery.
- Production modules: `aj/recovery.py`, `aj/lease.py`, `aj/journal.py`, `aj/task.py` (SQLite/WAL persistence), `aj/orchestrator.py`.

## Master crash points (1–16) — mapping (preliminary)
| Point | Scenario (as required) | Existing code/test evidence | Status | Gap / next proof |
|---|---|---|---|---|
| 1 | Crash before task persisted/committed | TaskStore SQLite persistence; transitions saved; no explicit kill-before-commit subprocess test found | UNPROVEN | Add subprocess test: start create/transition, kill before commit boundary where controllable, verify no corrupt partial record on restart |
| 2 | Crash after task created before authorization/lease | Lifecycle tests + recovery paths | PARTIALLY PROVEN | Need controlled interruption proof |
| 3 | Crash while acquiring execution/operation lease | `lease.py` atomic/lock behavior; expiry/break tests (`test_expired_lease_no_mutation_authorised`, lease refusal/break paths) | PARTIALLY PROVEN | Subprocess kill during acquire path not explicitly tested |
| 4 | Crash after lease acquired before execution starts | Lease held/expiry handling in recovery tests | PARTIALLY PROVEN | Controlled interruption proof needed |
| 5 | Crash during execution/attempt start | `test_crash_simulate_before_lease_release` simulates mid-flight state; retry scheduling crash covered | PARTIALLY PROVEN | Real subprocess interruption during handle/start_attempt needed |
| 6 | Crash during heartbeat renewal | `test_crash_during_heartbeat_renewal` (simulated state consistency) | PARTIALLY PROVEN | Kill during renew write path not externally supervised |
| 7 | Crash before lease release after work | `test_crash_simulate_before_lease_release` | PARTIALLY PROVEN | External kill proof |
| 8 | Crash after receipt/result persistence | `test_crash_after_receipt_persistence` (receipt truncation/state survival) | PARTIALLY PROVEN | Subprocess kill immediately after receipt write |
| 9 | Crash before final journal/task completion record | Journal append-only + reconciliation test; simulated state mutations | PARTIALLY PROVEN | Explicit kill-window test |
| 10 | Crash during retry scheduling | `test_crash_during_retry_scheduling` | PARTIALLY PROVEN | Subprocess kill during retry transition |
| 11 | Crash during dead-letter/requeue/abandon transition | Dead-letter tests cover transitions; crash during transition not explicitly kill-tested | PARTIALLY PROVEN | Targeted interruption test |
| 12 | Crash during dependency evaluation/blocking | `test_crash_during_dependency_evaluation` | PARTIALLY PROVEN | Subprocess kill at evaluation boundary |
| 13 | Crash with stale lease held by dead worker | `test_multi_process_lease_reclamation`, expiry/refusal/break tests | PROVEN (behavioral) | Multi-process reclaim covered; external kill of holder process covered indirectly |
| 14 | Crash during recovery itself | `test_repeated_recovery_is_idempotent_failed`, `test_repeated_recovery_after_restart` | PARTIALLY PROVEN | Kill recovery process mid-run |
| 15 | Concurrent recovery vs completion/races | `test_recovery_versus_normal_completion_race`, `test_multi_process_recovery_same_operation` | PROVEN (behavioral, multiprocessing) | Deterministic outcomes observed; external supervised kill variant optional |
| 16 | Restart after any interrupted state | Multiple reopen/recovery tests across suite; persistence verified | PARTIALLY PROVEN | Needs systematic per-point restart verification |

## Reconciliation states A–F — mapping (preliminary)
| State | Description (intent) | Evidence | Status | Gap |
|---|---|---|---|---|
| A | Task/journal/receipt consistent completed state | `test_journal_receipt_reconciliation_production_code`, normal completion paths | PARTIALLY PROVEN | Explicit state-label assertions per spec |
| B | Task incomplete, receipt/result evidence exists | Receipt persistence/truncation handling | PARTIALLY PROVEN | Construct exact state and verify recovery decision |
| C | Journal indicates progress but task state stale | Journal append + recovery classification | PARTIALLY PROVEN | Explicit construction/test |
| D | Lease held/stale but worker dead | Lease expiry/reclamation tests | PROVEN (behavioral) | — |
| E | Duplicate/retry/idempotent replay after interruption | Idempotent replay + retry + dead-letter suites | PROVEN (behavioral) | — |
| F | Conflicting/inconsistent evidence requiring safe halt/manual attention | Recovery classification `RECOVERY_REQUIRED` paths | PARTIALLY PROVEN | Explicit conflicting-state construction and safe outcome proof |

## Honest conclusion (current)
- **Operational reliability:** strong on current suite (199/199), with real persistence/WAL, lease handling, retry/dead-letter/idempotency, and several crash/race simulations.
- **Strict master-spec proof:** **not yet complete**. Many points are behaviorally covered but not proven via controlled external subprocess interruption at each enumerated boundary, and A–F states are not all explicitly enumerated as dedicated tests.
- **Next:** add targeted subprocess kill/restart tests for highest-risk uncovered points (1,4,5,7,8,9,10,14 and explicit B/C/F state constructions), using production CLI/runtime entry points and temp data dirs; document evidence per point.

## Additional subprocess-boundary evidence added (2026-11-10)
- `AJ/tests/test_inbox_subprocess_recovery.py::test_subprocess_capture_process_and_restart_visibility` (**PASS**, included in 200-suite): production CLI subprocess captures/processes, fresh subprocess reads persisted READY state + extracted/original artifacts from SQLite WAL store. This is real process-boundary restart visibility evidence for the inbox subsystem (Phase 2), not direct proof of AJ task crash points 1–16.
- Existing `tests/test_crash_safety.py` already includes multiprocessing-based recovery/lease/race cases (`test_multi_process_recovery_same_operation`, `test_multi_process_lease_reclamation`, `test_recovery_versus_normal_completion_race`, `test_repeated_recovery_after_restart`), providing cross-process behavioral evidence for points ~13/15/16 aspects, but explicit controlled kill at each enumerated AJ operation boundary remains incomplete.

## Evidence inventory snapshot (2026-11-10 continuation)
- `tests/test_crash_safety.py` (14 tests, multiprocess/recovery-oriented): covers expired lease mutation refusal, repeated recovery idempotency (failed/non-terminal cases), crash-simulation via persisted-state mutation + restart/recovery, lease expiry/break/reclaim, receipt persistence, heartbeat/renewal, retry scheduling, dependency evaluation, completed-task recovery no-op, multi-process recovery/lease reclamation, recovery-vs-completion race, repeated recovery after restart, journal/receipt reconciliation in production code paths. (Behavioral/multiprocess evidence; not a 1:1 `SIGKILL` at every enumerated master crash instruction boundary.)
- `tests/test_inbox_subprocess_recovery.py`: real CLI subprocess capture→fresh subprocess restart visibility (Phase 2 inbox boundary).
- **Classification remains:** AJ **200/200 operationally green**; **strict 1–16/A–F external kill-boundary coverage = VERIFICATION REQUIRED**. Priority feasible gaps to target next: 4,5,7,8,9 then 1,10,14 with explicit A–F constructions where safe/deterministic.


## 2026-11-11 bounded continuation note

- **No new external kill/subprocess interruption proofs added this segment.** Priority remained F2/F3/F4/F5 code/test/doc hardening (scheduler/resume authorization safety, evidence matrices). Existing deterministic multiprocess crash-safety coverage (14 tests in `AJ/tests/test_crash_safety.py`) and inbox restart-visibility test remain **VERIFIED** and full AJ suite is green (217 passed).
- **Step C status (bounded):** crash points **4,5,7,8,9,1,10,14** and A–F external-kill boundary proofs remain **VERIFICATION REQUIRED / NOT PRACTICALLY REPRODUCIBLE** in this environment without non-invasive, boundary-accurate interruption hooks. Alternative evidence: lease expiry/ownership semantics, receipt/journal/idempotency stores, retry/recovery refusal safety, and crash-safety test scenarios documented above.
- **Next concrete bounded work:** implement deterministic interruption at receipt-write/lease-release/state-commit boundaries only where harness can target real production paths without invasive refactors; classify each attempted point with pre-state, interruption method, fresh-process inspection, and invariants.


## 2026-11-11 gap-closure continuation (subprocess boundary constructions, 272-suite)

**Evidence added:** `AJ/tests/test_step_c_subprocess_crash_matrix.py` (12) + `AJ/tests/test_step_c_gap_closure.py` (8) — total 20 real subprocess/signal/persistence/boundary-construction tests this session. Full suite **272 passed, 0 failed**; `aj --check` exit 0. No production code changes required for passing evidence.

| Point | Updated evidence | Classification | Honest gap/limitation |
|---|---|---|---|
| 1 | Torn/malformed append and interrupted-write tests show no loss of prior committed records; no corrupt valid partial task from torn trailing fragment. Exact kill-before-first-commit at internal create boundary not externally timed. | **PARTIAL** | Precise pre-commit kill window not instrumented; no silent fabricated commit observed. |
| 2 | Lifecycle transitions + recovery; authorized/lease boundary constructions (point 4) cover adjacent state. | **PARTIAL** | Controlled external interruption at exact create→authorize boundary not timed. |
| 3 | Existing lease acquire/refusal/reclaim tests + concurrent lease serialization subprocess evidence. | **PARTIAL** | Kill during acquire syscall/write path not externally timed. |
| 4 | `test_point4_crash_after_execution_lease_acquired_before_execution` (real `os._exit` after lease+journal persist, AUTHORIZED) + fresh recovery/inspect. | **PASS (constructed boundary)** | Timed kill inside `acquire` implementation not separately forced; constructed state is explicit and deterministic. |
| 5 | `test_point7_crash_after_attempt_started_before_lease_release` (attempt started, EXECUTING, lease held, journal) + SIGKILL leased-worker test. | **PARTIAL→PASS for constructed states** | Not a timed kill at every in-flight execution instruction/side-effect boundary. |
| 6 | Existing heartbeat-renewal simulation in `test_crash_safety.py`. | **PARTIAL** | No externally timed kill during heartbeat write/renew path. |
| 7 | `test_point7_crash_after_attempt_started_before_lease_release`, `test_sigkill_worker_holding_lease_then_fresh_recovery`. | **PASS (constructed boundary + real kill)** | Exact post-work/pre-release internal micro-boundary not hook-instrumented beyond constructed state. |
| 8 | `test_point8_9_receipt_and_journal_present_but_task_not_completed_then_crash` (receipt+journal evidence persisted, task non-terminal). | **PARTIAL** | Exact AJ commit ordering window (receipt write vs final task completion transition) not forced by fault-injection hook. |
| 9 | Same constructed evidence-vs-completion boundary as 8/9; journal append persisted. | **PARTIAL** | Same micro-boundary limitation. |
| 10 | `test_point10_crash_during_retry_scheduling_state_then_recover` (persisted RECOVERING/RETRYING interruption) + existing retry scheduling simulation. | **PARTIAL** | Kill inside transition/scheduling code path not timed externally. |
| 11 | Dead-letter transitions covered by existing tests; no new external kill proof. | **PARTIAL / NOT VERIFIED (external kill boundary)** | Requires targeted deterministic interruption test or hook. |
| 12 | Dependency evaluation simulation in existing crash-safety tests. | **PARTIAL** | No externally timed subprocess kill at evaluation boundary. |
| 13 | Multiprocess lease reclamation/expiry tests + D construction (dead worker holding lease, fresh recovery). | **PASS (behavioral/constructed)** | — |
| 14 | `test_point14_crash_during_recovery_then_repeated_recovery_converges` (SIGKILL recovery subprocess + repeated recovery) + existing repeated recovery tests. | **PASS** | Timed kill at arbitrary recovery-internal instruction not forced; real interrupted recovery process evidenced. |
| 15 | Existing recovery-vs-completion race and multi-process recovery tests. | **PASS (behavioral, multiprocessing)** | — |
| 16 | Repeated crash/restart cycles, fresh-process visibility, reopen/integrity across multiple suites. | **PASS (process-boundary restart evidence)** | Not every interrupted state variant enumerated. |

| State | Updated evidence | Classification |
|---|---|---|
| A | `test_reconciliation_A_consistent_completed_state` + existing completion/reconciliation evidence. | **PASS** |
| B | Receipt/result evidence behaviors exercised partially (point 8/9 construction), but not explicitly labeled/constructed as mandated B recovery decision proof. | **PARTIAL** |
| C | Journal/progress persistence exists; explicit constructed "journal progress but task state stale" + mandated recovery decision not fully proven. | **PARTIAL** |
| D | `test_reconciliation_D_stale_lease_dead_worker_fresh_process` + lease expiry/reclamation tests. | **PASS** |
| E | `test_reconciliation_E_repeated_recovery_idempotent_replay_safe` + idempotent replay/retry suites. | **PASS** |
| F | `RECOVERY_REQUIRED`/safe-halt paths exist; explicit conflicting-evidence construction with mandated safe outcome not exhaustively proven. | **PARTIAL** |

**Defensible checkpoint:** Step C materially advanced; further closure of 1/3/6/8/9/10/11/12 internal micro-boundaries and exhaustive B/C/F constructions needs either test-only fault-injection seams (documented, non-production) or a crash-consistency/power-fault harness. Ordinary subprocess testing cannot prove power-loss/fsync durability boundaries. **P1-C remains PARTIAL / VERIFICATION REQUIRED.**
