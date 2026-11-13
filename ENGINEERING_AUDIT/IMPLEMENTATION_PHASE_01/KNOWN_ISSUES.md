# Known Issues

Ordered by what would bite next. None of these prevented this phase from being verified.

## Functional gaps (deliberate)

1. **No free-form execution command.** `python -m aj` exposes `--check`, `--demo`, `--list-capabilities`, `--version`. There is no `aj run "<goal>"`; only `aj.echo`/`aj.health_check` can execute. This is intentional until capability contracts are reviewed.
2. **No task/audit/memory query commands.** `tasks.jsonl` is append-only and has no reader; `AuditLog.recent()` is in-process only; `MemoryStore.events()` has no CLI. Inspecting history currently requires reading the files or writing a small script.
3. **Task store does not reload.** `TaskStore` holds records in memory and appends to JSONL; a new process starts empty. Crash recovery is therefore "history is on disk", not "state is resumed".
4. **Summaries are not produced.** The memory contract and enforcement exist, but nothing generates a summary yet, so `verify()` is trivially green in normal use.
5. **`--list-capabilities` probes loopback.** The JARVIS/HELIX adapters perform a TCP reachability check (`127.0.0.1:8875`, `:8765`). It is local only, but it is a socket operation; it should not be mistaken for a network-free path. `--check` does not probe them.

## Correctness/consistency notes

6. **Agent status key mismatch.** `HttpAgentAdapter.describe()` reports `reachable`, not `available`; `UnconfiguredAgent` reports `available`. Consumers must read both keys. Cosmetic today, confusing later.
7. **Delegated failure semantics unchanged.** A JARVIS/HELIX task with no adapter still reaches `FAILED` with `agent_unavailable`/`rejected`. That is honest but means the demo path is the only success path.
8. **Audit directory resolution.** `Aj` now builds its sink from `core.audit_dir`, but `AuditLog()` constructed directly elsewhere still defaults to `DEFAULT_AUDIT_DIR`. One authority would be better.
9. **Config precedence not fully tested.** Defaults < file < env < overrides is implemented; only file loading (including `$` comments) and default resolution were exercised. Env parsing edge cases (`__` nesting, coercion of `""`/`null`) are untested.
10. **`aj.config.json` `$comment` fix is new behaviour.** Unknown non-`$` sections are still rejected; only `$`-prefixed keys are ignored. No test asserts this yet — it was verified by direct load.

## Verification gaps

11. **Python 3.14.4 only.** `requires-python >=3.10` is declared but 3.10–3.13 were not run.
12. **No linter, formatter or type checker.** None was installed; style/type regressions would not be caught.
13. **No coverage measurement.** 76 tests pass, but coverage of `agents.py`, `integrations/gsconnect.py` and error branches in `orchestrator.py` is partial.
14. **Packaging artifacts present.** `.venv/` and `aj_control_plane.egg-info/` exist locally and are ignored by `.gitignore`; they are not source.
15. **No CI.** Nothing runs the suite automatically.
