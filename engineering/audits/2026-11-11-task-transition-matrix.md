# Task Transition Matrix (evidence-based, 2026-11-11)

Source of truth: `AJ/aj/task.py` (`TRANSITIONS`, `TaskRecord.transition/can_transition`, terminal states). Validation is enforced in `TaskRecord.transition()` (raises `AjError` with `CALLING_INVALID_STATE` on illegal transition unless `force=True`) and `TaskStore.transition()` persists via `save()`.

## States
`RECEIVED, UNDERSTANDING, PLANNED, WAITING_FOR_APPROVAL, AUTHORIZED, BLOCKED, EXECUTING, DELEGATED, VERIFYING, COMPLETED, FAILED, CANCELLED, ABORTED, RECOVERY_REQUIRED, RETRYING, RECOVERING, DEAD_LETTER`  
Terminal: `COMPLETED, FAILED, CANCELLED, ABORTED, RECOVERY_REQUIRED, DEAD_LETTER`.

## Permitted transitions (from code)
| From | Permitted to | Validator | Persistence | Evidence |
|---|---|---|---|---|
| RECEIVED | UNDERSTANDING, CANCELLED, FAILED, ABORTED, DEAD_LETTER | `task.transition` | `TaskStore.save` on transition | task `events` history; journal/audit vary by caller |
| UNDERSTANDING | PLANNED, BLOCKED, CANCELLED, FAILED, ABORTED, DEAD_LETTER | same | same | same |
| PLANNED | AUTHORIZED, WAITING_FOR_APPROVAL, BLOCKED, CANCELLED, FAILED, ABORTED, DEAD_LETTER | same | same | handle/resume emit journal/audit on auth/approval/deny |
| WAITING_FOR_APPROVAL | AUTHORIZED, CANCELLED, FAILED, ABORTED, DEAD_LETTER | same | same | approval decisions audited in orchestrator paths |
| AUTHORIZED | EXECUTING, CANCELLED, ABORTED, RECOVERY_REQUIRED | same | same | execution/recovery paths emit journal/audit/receipts |
| BLOCKED | AUTHORIZED, PLANNED, CANCELLED, FAILED, DEAD_LETTER, RECOVERY_REQUIRED | same | same | scheduler resume now routes BLOCKED->PLANNED for auth re-eval when needed |
| EXECUTING | DELEGATED, VERIFYING, COMPLETED, FAILED, CANCELLED, ABORTED, RECOVERY_REQUIRED, DEAD_LETTER | same | same | `_execute`, recovery/dead-letter paths |
| DELEGATED | VERIFYING, EXECUTING, COMPLETED, FAILED, CANCELLED, ABORTED, RECOVERY_REQUIRED, DEAD_LETTER | same | same | execution/verification paths |
| VERIFYING | COMPLETED, FAILED, CANCELLED, ABORTED, RECOVERY_REQUIRED, DEAD_LETTER | same | same | verification/completion paths |
| FAILED | RETRYING, RECOVERING, DEAD_LETTER, CANCELLED | same | same | retry/recover/dead-letter paths |
| RECOVERY_REQUIRED | RECOVERING, DEAD_LETTER, CANCELLED | same | same | recover paths |
| RETRYING | RECOVERING, EXECUTING, FAILED, CANCELLED, ABORTED, DEAD_LETTER, RECOVERY_REQUIRED | same | same | retry execution/recovery |
| RECOVERING | EXECUTING, VERIFYING, COMPLETED, FAILED, CANCELLED, ABORTED, DEAD_LETTER, RECOVERY_REQUIRED | same | same | recovery execution/verification |
| Terminal | none (unless `force=True`) | `task.transition` blocks | n/a | terminal guard prevents non-forced changes |

## Rejected transitions
- Any transition not in `TRANSITIONS[from]` raises `AjError` (`illegal transition ...`) — **VERIFIED by code**; exercised by existing suite and by new resume fix (BLOCKED->WAITING_FOR_APPROVAL was rejected, fixed via BLOCKED->PLANNED->WAITING_FOR_APPROVAL).
- Terminal states reject further transitions unless `force=True` — **VERIFIED by code**.

## Observed gaps / verification status
- **PARTIAL:** not every permitted transition has a dedicated positive/negative test; critical security-relevant paths (handle auth, retry/recover refusal, scheduler resume auth/refusal, crash recovery cases) are **VERIFIED by targeted tests**.
- **VERIFICATION REQUIRED:** exhaustive proof that no production path mutates `record.status`/persists state without `TaskRecord.transition`/`TaskStore.transition` validation; partial-write atomicity of task+auxiliary records is not guaranteed by a single transaction (JSON/filesystem stores).
- **Recovery behavior:** `recover`/`retry`/`dead_letter` enforce preconditions and transition rules in orchestrator; deterministic crash-safety tests cover key recovery/idempotency/lease scenarios (14 tests) — **PARTIALLY VERIFIED**.
