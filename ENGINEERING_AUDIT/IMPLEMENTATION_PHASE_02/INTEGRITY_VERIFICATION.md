# Integrity Verification — Phase 02

## Correlation across stores

For the verified `aj.echo` run:

| Store | Records | Task id |
|---|---|---|
| Task log | `tasks.jsonl`, `COMPLETED` with 6 transitions | `aj_20261110T094612_acd3d291` |
| Audit | `task_received`, `authorized`, `executed` | same |
| Memory | `task.created`, `task.authorized`, `task.completed` | same |

`test_audit_and_memory_share_the_task_id_and_lifecycle` asserts:

- the audit actions contain `task_received`, `authorized`, `executed`;
- every audit event's `task_id` equals the returned outcome id;
- memory kinds contain `task.created`, `task.authorized`, `task.completed`;
- every raw event's `task_id` equals the outcome id.

The task reload test independently confirms the same id after a fresh `TaskStore`.

## Audit integrity

| Property | Evidence |
|---|---|
| Append-only | `JsonlAuditSink` opens with `O_APPEND`; no rewrite/delete API exists |
| Private | files created `0600`, verified in the pre-existing JSONL sink test and in the isolated demo |
| Redacted before persistence | `test_audit_redacts_secrets_and_keeps_required_fields`; new `read_events()` check asserts `api_key` reads back as `[redacted]` |
| Malformed lines | counted by `read_events()` and reported by the CLI; never removed |
| No secrets in CLI output | audit query prints action/agent/task/result only; `--json` returns stored (already redacted) events |

## Memory integrity

| Property | Evidence |
|---|---|
| Raw canonical, append-only | no delete API; store test proves summaries do not replace events |
| Citation enforcement | summary with missing ids rejected; `verify()` reports simulated corruption |
| Reopen persistence | raw event survives closing and reopening the database |
| Summary rebuild | identical content; raw hash unchanged |
| Provenance | `source`, `task_id`, `meta`, `at` preserved and printed |

## Cross-process consistency

The CLI verification used a separate process for `run`, then for `tasks`/`task`/`audit`/`memory`/`recover`. All read the same ids and states from disk. No in-memory continuation was assumed.

## Test isolation

Real state before/after the full suite:

```
audit lines 9 → 9
task lines  7 → 7
```

All tests use temporary directories or an isolated `--config`; `--check` uses temporary or in-memory stores. No test wrote to `~/.local/share/aj/`.
