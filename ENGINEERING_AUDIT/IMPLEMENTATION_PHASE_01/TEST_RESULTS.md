# Test Results

## Environment

| Item | Value |
|---|---|
| Interpreter | Python 3.14.4 (`/usr/bin/python3`, venv at `AJ/.venv`) |
| pytest | 9.2.0 (installed into the venv only) |
| Network | not used by any test |
| Provider credential | none required |

## Baseline — existing suite, before any code change

Command: `.venv/bin/python -m pytest tests -q`

```
65 passed in 0.40s
exit 0
```

The audit's statement "AJ's suite has never run" is now resolved: **65/65 passed unmodified**. No test was rewritten, skipped, xfailed, or weakened.

## Final — full suite

Command: `.venv/bin/python -m pytest -q`

```
76 passed in 0.67s
exit 0
```

Test selection by file (`--collect-only`):

| File | Tests |
|---|---:|
| `test_foundation.py` | 20 |
| `test_calling.py` | 10 |
| `test_hermes_contract.py` | 7 |
| `test_memory.py` | 6 |
| `test_orchestrator.py` | 13 |
| `test_providers.py` | 7 |
| `test_runtime.py` (new) | 11 |
| **Total** | **76** |

## New tests and what each proves

| Test | Proves |
|---|---|
| `test_end_to_end_lifecycle_audits_and_persists_raw_events` | task → permission ALLOW → capability lookup → `aj.echo` execution → audit `task_received/authorized/executed` → raw events `task.created/authorized/completed` → `COMPLETED` with output |
| `test_permission_gate_blocks_consequential_capability_until_approved` | level-3 capability produces `WAITING_FOR_APPROVAL`, nothing executes, no `task.completed` event; approval then completes |
| `test_forbidden_capability_aborts_before_any_execution` | forbidden capability → `ABORTED`, no execution |
| `test_missing_capability_fails_with_a_specific_code` | unknown capability → `FAILED`, `capability_not_found` |
| `test_action_failure_marks_the_task_failed_and_is_audited` | action exception → `FAILED`, `execution_failed`, message preserved, audit + memory failure events |
| `test_invalid_task_is_rejected_and_no_record_is_created` | empty goal refused before a record exists |
| `test_health_check_passes_with_no_network_agents_or_credentials` | all 10 checks green; `attached` all false/NOT ATTACHED |
| `test_cli_check_runs_as_a_module` | `python -m aj --check` exits 0 and prints valid JSON |
| `test_demo_proves_the_whole_lifecycle_and_persists_records` | demo outcome ok, output correct, ≥3 raw events in order, persisted store |
| `test_mock_provider_completes_without_network_or_credentials` | `MockProvider` returns text, records the request |
| `test_mock_provider_failure_is_normalised_and_does_not_fall_through` | injected failure surfaces as `provider_unavailable`, no fallback to success |

## Failure classification

| Category | Count |
|---|---|
| Environment failure | 0 |
| Missing dependency | 0 (pytest installed into the venv) |
| Import failure | 0 |
| Implementation bug | 0 |
| Stale test | 0 |
| Architectural mismatch | 0 |

No test was unable to run. There are no skips and no warnings that affect results.
