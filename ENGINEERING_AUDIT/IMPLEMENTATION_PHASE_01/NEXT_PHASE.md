# Next Phase

## Where AJ actually stands

- Runnable: `python -m aj --check` (10/10), `--demo` (full lifecycle), `--list-capabilities`.
- Tested: 76 tests, 65 of them pre-existing and untouched.
- Honest: JARVIS, HELIX, Hermes, Honcho and every provider are absent and reported as absent.
- Local: SQLite raw events, JSONL tasks, JSONL audit (0600).
- Not integrated, not deployed, not version-controlled.

## Recommended next phase: **Operate the foundation** (small, local, no integration)

Goal: make AJ usable for real local work without a demo flag, still with zero sub-agents.

1. **Task/audit/memory read surface**
   - `aj task status <id>` and `aj task list` reading `tasks.jsonl` (append-only replay, latest record wins).
   - `aj audit tail [-n N]` reading the configured audit directory.
   - `aj memory query --kind … --task … --since …` over `MemoryStore.events()`.
2. **A single, explicit execution command**
   - `aj run "<goal>" --capability aj.echo --text "…"` limited to capabilities whose `execution_adapter` starts with `internal:`.
   - Refuse anything else with `capability_unavailable`, naming why. This keeps the command honest and useful.
3. **Config correctness tests**
   - File/env/override precedence, `$` comment keys, unknown-section rejection, invalid value errors.
4. **A summary path that proves the derived layer**
   - Generate one deterministic summary over a task's raw events, cite ids, then delete only the summary and rebuild it — proving rebuildability without touching canonical rows.
5. **Recovery/retention note**
   - Document that `tasks.jsonl` is history, not resumable state; decide whether a `--resume` loader is in scope.

Acceptance: every command works offline, every mutation is audited, no sub-agent needed, suite still green.

## Explicitly later (each needs A3)

| Step | Why it waits |
|---|---|
| JARVIS/HELIX `AgentRequest` endpoint | external code, running systems, protocol agreement |
| Hermes execution adapter | HERMES GREEN SIGNAL; unproven writer history |
| Honcho memory adapter | canonical rule says optional; writer test still outstanding |
| Live provider adapter test | cost authorization |
| Git baseline for AJ | owner decision |
| Any service/daemon/deploy | out of scope by design |

## What must not happen next

- Do not attach sub-agents "to make the demo more impressive".
- Do not let AJ write to Honcho.
- Do not promote capability declarations to `verified` without evidence.
- Do not add Docker, Redis, Celery or a web server to a single-user laptop foundation.
