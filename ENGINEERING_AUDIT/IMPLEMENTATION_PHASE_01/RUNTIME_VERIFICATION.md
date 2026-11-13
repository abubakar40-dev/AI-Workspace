# Runtime Verification

All commands run from `AI_WORKSPACE/AJ` with `.venv/bin/python` unless stated.

## 1. Self-check — `python -m aj --check`

Exit code **0**. `ok: true`, `version: 0.1.0`.

| Check | Detail |
|---|---|
| imports | 20 modules imported |
| configuration | 9 sections; `data_dir=/home/abubakargcx/.local/share/aj`; `unattended_ceiling=1` |
| task_lifecycle | task reached `COMPLETED`, `terminal: true` |
| permissions | read=`allow`, consequential=`confirm`, forbidden=`deny` |
| capabilities | 2 internal capabilities registered and executable |
| audit | redaction confirmed (`api_key` → `[redacted]`) |
| memory | append/read/`verify()` ok on an in-memory store |
| providers | configured providers present, **0 usable**, gateway refuses with `provider_unavailable` |
| execution | `NOT ATTACHED`, requires HERMES GREEN SIGNAL |
| orchestrator | boots with no agents; `active_tasks=0`; execution `NOT ATTACHED` |

`attached`: `{"jarvis": false, "helix": false, "hermes": "NOT ATTACHED"}`.

The self-check uses an in-memory memory store and writes no file. It makes no network call, reads no credential, and needs no sub-agent.

## 2. Demo — `python -m aj --demo`

Exit code **0**.

```
status: COMPLETED | ok: True | output: {'echo': 'hello from AJ'} | capability: aj.echo
audit actions: ['task_received', 'authorized', 'executed']
memory: {'path': '.../aj/memory.sqlite3', 'raw_events': 3, 'summaries': 0}
memory events: [(1, 'task.created'), (2, 'task.authorized'), (3, 'task.completed')]
```

Task record transitions (from `tasks.jsonl`):

```
UNDERSTANDING -> PLANNED -> AUTHORIZED -> EXECUTING -> VERIFYING -> COMPLETED
```

This is the required end-to-end proof: task → permission → capability → execution → audit → memory → result → completion.

## 3. Capability listing — `python -m aj --list-capabilities`

Exit code **0**. 40 capabilities: 2 AJ internal (`aj.echo`, `aj.health_check`), 3 declared HELIX/Hermes/AJ entries from `config/capabilities.json`, and the imported JARVIS catalogue (25 tools plus the shipped declarations). Execution port reports `NOT ATTACHED`.

Note: this command performs the adapters' existing loopback reachability probes for JARVIS (`127.0.0.1:8875`) and HELIX (`127.0.0.1:8765`). Reachable ≠ task-capable; both adapters report no agreed AJ task endpoint.

## 4. Packaging and installed entrypoint

```
.venv/bin/python -m pip install -e ".[dev]"   # exit 0
cd /tmp && <AJ>/.venv/bin/aj --check          # exit 0, ok: true
```

The console script works outside the repository directory, so packaging metadata and the module entrypoint are correct.

## 5. CLI surface

```
usage: aj [-h] [--version] [--check] [--demo] [--list-capabilities]
          [--config CONFIG] [--log-level LOG_LEVEL]
```

Exit codes: `0` success, `1` failed check/demo or `AjError`, `2` no action requested (prints help).

## 6. Logging

`configure_logging()` installs one stderr handler on the `aj` logger, level from `runtime.log_level` or `--log-level`. No configuration values, tokens or payloads are logged. Debug output from failed health checks records only the exception type.
