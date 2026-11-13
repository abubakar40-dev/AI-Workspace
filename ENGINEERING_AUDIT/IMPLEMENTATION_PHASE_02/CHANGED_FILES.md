# Changed Files — Phase 02

`AI_WORKSPACE/AJ` is not a git repository, so this manifest is the change record.

## Added

| File | Lines | Purpose |
|---|---:|---|
| `AJ/aj/recovery.py` | 99 | `Finding`, `classify()`, `RecoveryManager.scan/recover`; replay-safety gate |
| `AJ/aj/summary.py` | 96 | deterministic digest, `build()`, summary `delete()`, `summaries()` |
| `AJ/tests/test_phase2.py` | 324 | 11 tests: restart, failure persistence, corruption, recovery (safe/unsafe), summary rebuild/integrity, correlation, health, CLI round-trip/refusals |

## Modified

| File | Lines now | Change |
|---|---:|---|
| `AJ/aj/task.py` | 375 | `RECOVERY_REQUIRED` state + transitions; `request_payload`; `reload()`, `save()`, `update()`, `query()`, `load_errors`; autoload on construction |
| `AJ/aj/capability.py` | 264 | `replay_safe` field (default `False`), serialised in `to_dict/from_dict` |
| `AJ/aj/actions.py` | 126 | `aj.echo`/`aj.health_check` declared `replay_safe=True`; echo accepts `message` or `text` |
| `AJ/aj/orchestrator.py` | 609 | persist request payload; `recover()` + `_require_manual_recovery()`; late-mutation saves on failure, internal, Hermes and delegated paths |
| `AJ/aj/audit.py` | 238 | `AuditReadResult` + `read_events()` with task/action/agent filters and malformed count |
| `AJ/aj/runtime.py` | 381 | six new checks: task persistence, audit reader, memory reader, recovery, summary, CLI |
| `AJ/aj/__main__.py` | 418 | subcommand CLI with run/tasks/task/audit/memory/capabilities/recover and `--json` |
| `AJ/README.md` | 134 | Phase 2 commands, persistence, recovery, summaries, invariants |

## Unchanged

`permissions.py`, `contracts.py`, `execution.py`, `agents.py`, `calling.py`, `memory.py` (store semantics untouched), `errors.py`, `ids.py`, `integrations/*`, `config/*.json`, `schemas/*`, `docs/*`, and the six pre-existing test modules.

## Generated

`.venv/` (pytest 9.2.0), `aj_control_plane.egg-info/`, `.pytest_cache/`, `__pycache__/` — all ignored.

## Verification-only paths (outside the project)

`/tmp/aj_p2_demo/` (isolated config, tasks, audit, memory) and pytest temporary directories. No real AJ state or other project was modified.
