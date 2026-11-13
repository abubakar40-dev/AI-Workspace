# Changed Files

`AI_WORKSPACE/AJ` is **not a git repository**, so this manifest is the change record.

## Added

| File | Lines | Purpose |
|---|---:|---|
| `AJ/pyproject.toml` | 21 | setuptools packaging, pytest config, `aj` console script, dev extra |
| `AJ/.gitignore` | 7 | ignore `.venv`, bytecode, caches, egg-info, build output |
| `AJ/aj/actions.py` | 123 | `InternalActions` registry, `echo`/`health_check`, `aj.echo`/`aj.health_check` declarations |
| `AJ/aj/runtime.py` | 266 | logging, memory path, `assemble()`, 10 health checks, `run_demo()` |
| `AJ/aj/__main__.py` | 82 | CLI: `--check`, `--demo`, `--list-capabilities`, `--version`, `--config`, `--log-level` |
| `AJ/tests/test_runtime.py` | 220 | 11 foundation tests (lifecycle, policy denial, forbidden, missing capability, action failure, invalid task, health, CLI subprocess, demo, mock provider success/failure) |
| `AJ/.venv/` | generated | local Python 3.14.4 venv with pytest 9.2.0 (ignored) |
| `AJ/aj_control_plane.egg-info/` | generated | editable-install metadata (ignored) |

## Modified

| File | Lines now | Change |
|---|---:|---|
| `AJ/aj/orchestrator.py` | 539 | internal execution branch; raw-memory `_remember()`; events on created/authorized/completed/failed/cancelled; `TaskOutcome.output`; `Aj(memory=, actions=)`; `build(memory=, actions=)`; internal specs registered; audit sink now uses `core.audit_dir` |
| `AJ/aj/config.py` | 225 | `core.memory_path`; `runtime.persist_memory`; `runtime.memory_filename`; `$`-prefixed comment keys ignored when loading a file |
| `AJ/aj/providers.py` | 361 | `MockProvider` implementing `ProviderAdapter` (`usable`, `complete`, injectable error, request log) |
| `AJ/tests/conftest.py` | 26 | `persist_memory=False` in the shared test config |
| `AJ/README.md` | 103 | rewritten: quick start, CLI table, lifecycle, module map, memory rules, provider boundary, explicit non-implementation |

## Not touched (verified by inspection)

`AJ/aj/task.py`, `permissions.py`, `capability.py`, `audit.py`, `memory.py`, `contracts.py`, `execution.py`, `agents.py`, `calling.py`, `errors.py`, `ids.py`, `integrations/*`, `config/*.json`, `docs/*`, `schemas/*`, and the five pre-existing test modules.

Outside AJ: nothing was modified. Runtime state written by the demo lives only in `~/.local/share/aj/` (AJ's own data directory): `memory.sqlite3`, `tasks.jsonl`, `audit/events-2026-11.jsonl`.
