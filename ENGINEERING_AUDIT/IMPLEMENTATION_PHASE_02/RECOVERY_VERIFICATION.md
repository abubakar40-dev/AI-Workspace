# Recovery Verification — Phase 02

## Policy

A persisted non-terminal task is replayed only when **all** hold:

1. its capability is registered;
2. the capability's adapter is an internal action (`internal:*`);
3. the capability declares `replay_safe=True` (default `False`).

Otherwise the task is marked `RECOVERY_REQUIRED`, `requires_user_decision=True`, and nothing executes.

`aj.echo` and `aj.health_check` declare `replay_safe=True`. `aj.delegate` (adapter `aj.orchestrator`), every JARVIS tool and every HELIX capability declare or default to `False`.

## Verified: unsafe detection and refusal

Setup: task in `AUTHORIZED` with capability `aj.boom` (internal adapter, `replay_safe=False`) and a task in `PLANNED` with `jarvis.web_search`.

```
aj recover
→ aj_…4c7746c4  AUTHORIZED  replay_safe        internal action declared replay-safe
→ aj_…a60f9729  PLANNED     recovery_required  capability is not an internal action
→ recovered aj_…4c7746c4: COMPLETED
```

Explicit unsafe attempt:

```
aj recover --task aj_…a60f9729
→ RECOVERY_REQUIRED (Recovery required: capability is not an internal action)
→ exit 1
```

Verification:

- no `executed` audit event for the unsafe task;
- `recovery_refused` audit event present;
- task state is `RECOVERY_REQUIRED` in a later process;
- no JARVIS/HELIX call was attempted.

## Verified: safe replay

Setup: interrupted `aj.echo` task in `EXECUTING` with `request_payload={"text":"recover me"}`.

| Invariant | Result |
|---|---|
| Task id unchanged | yes |
| Prior transitions preserved | exact prefix equality in test |
| New events appended | `EXECUTING → VERIFYING → COMPLETED`, plus audit `recovery_started` and raw `task.recovery` |
| Output correct | `{"echo": "recover me"}` |
| Second replay refused | `AjError` because the task is terminal |
| No duplicate side effect | only one completion; only one `executed` audit event |

A fresh CLI process after recovery (`aj task <safe-id>`) showed `COMPLETED` with the full history, proving replay is persisted, not just in-memory.

## Recovery of failed tasks

Only non-terminal tasks are scanned. `FAILED` is treated as a bounded recovery path through the existing `retry()` API, not automatic replay; `aj recover` does not touch it.

## Limits

- Recovery increments `attempt` without consulting `max_attempts`; it is an explicit human action, not an automatic retry loop.
- Recovery relies on the persisted `request_payload`. Tasks created before Phase 2 have an empty payload, so a replay would use the goal text only; they are not selected automatically unless their capability is replay-safe, and their output may be empty.
- No automatic recovery at startup: the operator must run `aj recover`. This is deliberate.
