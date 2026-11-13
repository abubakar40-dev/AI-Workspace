# CLI Verification — Phase 02

All commands were run against an isolated config at `/tmp/aj_p2_demo/aj.config.json` (data, audit and memory under `/tmp/aj_p2_demo/data`), so no real AJ state was used.

## `aj run`

```bash
python -m aj --config …/aj.config.json run \
  --capability aj.echo --input '{"message":"phase 2 test"}'
```

```
Task: aj_20261110T094612_acd3d291
Capability: aj.echo
Status: COMPLETED
Summary: aj.echo completed
Output: {"echo": "phase 2 test"}
```

Exit 0. `aj run "echo hello"` maps deterministically to `aj.echo`; `--text hello` is shorthand for `{"text":"hello"}`.

## `aj tasks`

```
TASK ID                            STATUS               CAPABILITY               CREATED
aj_20261110T094612_acd3d291        COMPLETED            aj.echo                  2026-11-10T09:46:12+05:00
```

Filters verified: `--status AUTHORIZED`, `--status PLANNED`, `--limit`, `--json`. `--json` also returns `load_errors`.

## `aj task <id>`

```
Task: aj_20261110T094612_acd3d291
Status: COMPLETED
Goal: run aj.echo
Requester: cli  Owner: AJ
Capability: aj.echo
Summary: aj.echo completed
Transitions:
  UNDERSTANDING (routed to AJ (explicit capability))
  PLANNED (explicit capability)
  AUTHORIZED (read-only: allowed unattended)
  EXECUTING (AJ:aj.echo)
  VERIFYING (internal action returned)
  COMPLETED (internal:echo)
```

This was run in a **separate process** from the `run` command, proving reload from disk.

## `aj audit`

```
2026-11-10T09:46:12+05:00  task_received  AJ  aj_…acd3d291
2026-11-10T09:46:12+05:00  authorized     AJ  aj_…acd3d291  authorized
2026-11-10T09:46:12+05:00  executed       AJ  aj_…acd3d291  completed
```

Filters `--task`, `--event`, `--agent`, `--limit`, `--json` implemented. Malformed lines are counted and reported to stderr; the file is never rewritten.

## `aj memory`

```
   ID  WHEN                       KIND               TASK              PREVIEW
    3  …09:46:12+05:00            task.completed     aj_…acd3d291      aj.echo completed
    2  …09:46:12+05:00            task.authorized    aj_…acd3d291      read-only: allowed unattended
    1  …09:46:12+05:00            task.created       aj_…acd3d291      run aj.echo
```

`--json` returns `events`, `path`, `exists` and store `stats`. Provenance (`id`, `at`, `kind`, `task_id`, `source`, `meta`) is preserved.

## `aj capabilities`

40 capabilities listed. Internal actions are visible with their replay declaration:

```
aj.echo           AJ  risk=0 verified  replay_safe=True
aj.health_check   AJ  risk=0 verified  replay_safe=True
aj.delegate       AJ  risk=1 verified  replay_safe=False
```

## `aj recover`

```
aj_…4c7746c4  AUTHORIZED  replay_safe        internal action declared replay-safe
aj_…a60f9729  PLANNED     recovery_required  capability is not an internal action
recovered aj_…4c7746c4: COMPLETED (aj.echo completed)
```

Explicit unsafe recovery:

```
python -m aj --config … recover --task aj_…a60f9729
→ recovered aj_…a60f9729: RECOVERY_REQUIRED (Recovery required: capability is not an internal action)
→ exit 1
```

## `aj --check`

16/16 checks pass: imports, configuration, task lifecycle, permissions, capabilities, audit, memory, providers, execution, task persistence, audit reader, memory reader, recovery, summary, CLI, orchestrator.

## Refusals

| Input | Result |
|---|---|
| `run --capability jarvis.web_search` | exit 1, `capability_unavailable` (not an internal action) |
| `run --capability aj.nope` | exit 1, `capability_not_found` |
| `run --capability aj.echo --input 'not json'` | exit 1, `config_invalid` |
| `recover --task <unsafe>` | exit 1, task marked `RECOVERY_REQUIRED`, no execution |

## Compatibility

`--check`, `--demo`, `--list-capabilities`, `--version`, `--config` and `--log-level` from Phase 1 still work. `--list-capabilities` is an alias for `capabilities`.
