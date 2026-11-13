# Test Results — Phase 02

## Environment

Python 3.14.4 (`AJ/.venv`), pytest 9.2.0, no network, no credentials, no sub-agents.

## Counts

| Measure | Value |
|---|---|
| Baseline tests (before Phase 2 changes) | **76 passed** |
| Phase 2 tests added | **11** |
| Total tests | **87 passed in 1.72s** |
| Failures | **0** |
| Skips / xfails | 0 |

Commands:

```bash
cd AI_WORKSPACE/AJ
.venv/bin/python -m pytest -q          # 87 passed
.venv/bin/python -m aj --check         # exit 0, 16/16 checks
```

## New Phase 2 tests

| Test | Proves |
|---|---|
| `test_task_survives_a_process_style_restart` | fresh `TaskStore` reads the same id, `COMPLETED`, payload and history; no load errors |
| `test_failed_task_is_persisted_with_its_error` | `FAILED` + `execution_failed` survive reload (regression for late-write defect) |
| `test_corrupted_record_is_reported_and_history_is_not_deleted` | valid task still loads; 2 malformed lines reported; file still has 3 lines |
| `test_interrupted_task_is_detected_and_never_blindly_replayed` | non-terminal detected; unsafe decision; `RECOVERY_REQUIRED`; no `executed` audit |
| `test_replay_safe_task_recovers_without_losing_history` | same id, prior events prefix unchanged, recovery/completed events appended, second replay refused |
| `test_summary_rebuild_is_deterministic_and_leaves_raw_events_untouched` | identical content twice; raw hash equal; delete/rebuild parity; 3 raw events remain |
| `test_audit_and_memory_share_the_task_id_and_lifecycle` | audit actions and memory kinds correlate on one task id |
| `test_health_includes_phase2_components` | six new checks present and green |
| `test_cli_run_inspect_and_query_round_trip` | `run → tasks → task → audit → memory → recover` all exit 0 with correct JSON |
| `test_cli_refuses_non_internal_capabilities` | `jarvis.web_search` refused, exit 1, typed error |
| `test_cli_rejects_unknown_capability_and_bad_input` | unknown capability and malformed `--input` both exit 1 |

## Failure classification during implementation

| Category | Count | Detail |
|---|---|---|
| Implementation bug | 1 | late persistence of errors/summary after status transition — fixed and covered |
| Environment / dependency | 0 | — |
| Import / stale test | 0 | — |

## Test isolation evidence

Full suite executed with the real state files measured before and after:

```
audit lines: 9 → 9
task lines:  7 → 7
```

All Phase 2 tests use `tmp_path` or an isolated `--config`. No test writes to `~/.local/share/aj/`.
