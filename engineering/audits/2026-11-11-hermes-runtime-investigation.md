# Hermes Runtime & AJ Integration Investigation (Step D, read-only)

**Date:** 2026-11-11  
**Scope:** READ-ONLY inspection only. No kill/restart/migrate/upgrade/reconfigure performed. No destructive skills executed. No secrets/credential values exposed.

## 1) Installation and version

- **CLI:** `/home/abubakargcx/.local/bin/hermes`
- **Version:** `Hermes Agent v0.23.0 (2026.9.24) · stable · local 2bd378ed1b8d`
- **Install dir:** `/home/abubakargcx/.hermes/hermes-agent` (git install)
- **Python/runtime:** `Python 3.14.9`, `OpenAI SDK 2.54.0`
- **Managed tools/env:** `~/.hermes/tools/python-3.14.9+20261021-linux-x64`, `~/.hermes/tools/node-26.12.1-linux-x64`, venvs under `~/.hermes/installs/...`
- **Home/config root:** `~/.hermes/` (config, auth, state DBs, logs, sessions, skills, whatsapp, gateway sockets/state, plugins/tooling)

## 2) Service and process state

- **systemd (user):** `hermes-gateway.service` — **loaded, enabled, active (running)** since `2026-11-09 02:23:28 PKT` (`~/.config/systemd/user/hermes-gateway.service`).
  - Exec: `.../hermes-agent/.hermes/bin/hermes gateway run` (WorkingDirectory `~/.hermes`, `HERMES_HOME=/home/abubakargcx/.hermes`, supervised/restart policy configured).
- **Observed processes (read-only, 2026-11-11):**
  - PID **548124** (PPID 1577), **`Ssl`**, ~2d uptime: Hermes gateway Python process (`.../python3 ... hermes_cli.main gateway run`).
  - PID **548360** (child of 548124), **`Ssl`**: WhatsApp bridge `node .../scripts/whatsapp-bridge/bridge.js --port 3000 --session ~/.hermes/whatsapp/session --mode self-chat`.
  - PID **548361** (child of 548124), **`Ss`**: `/bin/sh .../hermes_cli/process_supervisor.sh 548124`.
  - PID **918166** (separate, PPID 1577, **`Ssl`**): `/usr/bin/node /tmp/omnirush-hermes/src/proxy.mjs` (local OmniRush/OpenAI-compatible proxy component in `/tmp/omnirush-hermes`, distinct from gateway service tree).
- **Listeners/sockets (corrected by probe):**
  - **`127.0.0.1:33143`** (pid 548124) serves the **Hermes dashboard SPA** (`<title>Hermes Agent - Dashboard</title>`), and answers *every* path — including `/v1/health` and `/v1/skills` — with `200 text/html` + `/assets/*.js` bundle. It is therefore the **UI listener, not the `/v1` API**.
  - `~/.hermes/gateway.sock` — gateway **control socket** (CLI↔gateway lifecycle verbs: `identify`, `pause_for_update`, `rescan_profiles`, `serve_profile_hot`, `unserve_profile`, `migrate/purge_profile_identity`, `reload_plugins`, `session_ticket`). **Control only — no task submission.**
  - `~/.hermes/state/gateway.loop-tick.548124.sock` — internal loop-tick socket.
- **STAT T discrepancy (previously reported):** **NOT OBSERVED now.** No Hermes process in `T`/stopped-traced state found in current `ps` snapshot; active gateway/main/bridge/supervisor processes are running/sleeping normally. Cause/state of the earlier report cannot be retroactively determined from current evidence (possible transient trace/stop, prior process replaced, or stale observation). **Conclusion:** systemd active status alone was/is insufficient for health claims, but current process-level evidence shows the managed gateway tree running now.

## 3) Gateway/runtime health indicators (read-only)

- **Gateway state:** `~/.hermes/gateway_state.json` reports `gateway_state: "running"`, active gateway pid, whatsapp platform `connected` (updated 2026-11-08T21:23:41Z), `session_store.status: "ok"`, `active_agents: 0`, `active_work: null`, recent `updated_at` 2026-11-11T19:10:03Z.
- **Heartbeats/state:** `~/.hermes/state/gateway.heartbeat`, `gateway.lifecycle.json` present.
- **Logs (recent, redaction-safe):** `journalctl --user -u hermes-gateway.service` shows active request handling attempts failing at LLM/provider layer with **HTTP 402 credit/quota exhaustion** for `openrouter/auto` (and fallback free-model credential pools exhausted/cooldown), with structured non-retryable/billing errors and fallbacks attempted. **Interpretation:** gateway process and messaging/runtime are alive and processing, but successful end-to-end LLM completions are currently blocked by provider billing/credits/quota for configured models (not a proven gateway crash). WhatsApp bridge connectivity reported healthy in state.
- **CLI probes:** `hermes --help`, `hermes gateway --help` available (subcommands include run/ensure/start/stop/restart/status/install/uninstall/list/setup/migrate/enroll). `hermes status`/`hermes doctor` were not completed in this pass due to command timeout in the investigation shell (45s); treated as **NOT VERIFIED** here (no blocking read-only health summary captured beyond service/state/log/process evidence).

## 4) Configuration (redacted structure, no secret values)

- **Files:** `~/.hermes/config.yaml` (+ backups), `~/.hermes/auth.json` (present; contents not read/exposed), `~/.hermes/gateway_state.json`, `honcho.json`, `spawn-ledger.json`, `processes.json`, model/provider caches, etc.
- **Key settings (redacted):** `model.default=openrouter/auto`, provider `openrouter`; fallbacks include `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`, `openrouter/nvidia/nemotron-3.5-lightning:free`; gateway features (watchdogs, restart guards, multiplex, ledgers, etc.), WhatsApp enabled with configured home channel IDs, plugins enabled include `honcho`, skills/agent/memory/compression settings, `gateway.api_server` redacted. (Sensitive keys/tokens/secrets redacted in inspection.)

## 5) Data stores, memory, sessions, and runtime artifacts

- **State DBs:** `~/.hermes/state.db` (+ `-wal`, `-shm`, locks), `~/.hermes/projects.db`, `~/.hermes/kanban.db` (+ `-wal`, `-shm`, locks), `~/.hermes/cron/executions.db`.
- **Sessions/logs:** `~/.hermes/sessions/` (session JSON, request dumps), `~/.hermes/runtime/active_sessions.json`, extensive logs in `~/.hermes/logs/` (`agent.log`, `errors.log`, `gateway.log`, `gateway-exit-diag.log`, etc.).
- **Memories:** `~/.hermes/memories/` directory present (observed empty at top level in listing); canonical memory/state also represented in Hermes state DBs and session artifacts (detailed schema not exhaustively inspected read-only).
- **Messaging/platform state:** `~/.hermes/whatsapp/session` and bridge logs; `channel_directory.json`.

## 6) Skills, plugins, tools, and execution architecture (observed)

- **User/home skills:** `~/.hermes/skills/` contains curated/bundled/hub-managed skill trees (e.g. devops, research, productivity, web, autonomous-ai-agents, social-media, etc. with `SKILL.md`/references/scripts and `.hub` index/lock/scan artifacts).
- **Install skills/plugins:** `~/.hermes/hermes-agent/skills`, `optional-skills`, extensive `plugins/` (platforms, web, browser, memory, computer_use, image/video gen, cron providers, security-guidance, etc.) and tests/tools; Hermes codebase includes large gateway/session/state/agent modules (skill/tool execution, session workers, platform integrations).
- **Skill discovery/execution:** architecture present in Hermes codebase and home skill store; **live discovery/execution of a specific installed skill not exercised** in this read-only pass (avoids side effects, unreviewed skills, and provider/credential usage).

## 7) Interfaces (available/observed, with honest availability status)

Source-of-truth for the API surface: `gateway/platforms/api_server.py` (`_http_route_table`, docstring: *"OpenAI-compatible API server platform adapter (aiohttp); any OpenAI-compatible frontend connects at http://localhost:8642/v1 with API_SERVER_KEY"*).

| Interface | Transport | What it offers | Available **now** on this host? |
|---|---|---|---|
| `api_server` platform (`/v1`) | aiohttp HTTP, default port **8642** (configurable) | Durable task API: `POST /v1/runs`, `GET /v1/runs/{id}`, `GET /v1/runs/{id}/events` (SSE), `POST /v1/runs/{id}/{approval,steer,stop,clarify,resolve-unknown}`; discovery `GET /v1/{health,capabilities,skills,toolsets,models}`; also OpenAI-compatible `POST /v1/chat/completions`, `POST /v1/responses`, `GET/DELETE /v1/responses/{id}`, `GET /api/sessions`, `/api/jobs` | **NO — platform not enabled.** `platforms:` in `~/.hermes/config.yaml` enables only `whatsapp`. Requires `platforms.api_server.enabled: true` + `key` of ≥16 chars (`_has_usable_api_server_key`) → **config/permission change = out of approved scope**. |
| Gateway control socket | UNIX socket `~/.hermes/gateway.sock` | lifecycle/control verbs only (identify, restart-pause, profile serve/unserve, plugin reload, session ticket) | **YES** (control only; cannot submit a task) |
| Dashboard UI | loopback HTTP `127.0.0.1:33143` | Dashboard SPA; **not** `/v1` (probe: `GET /v1/health` → `200 text/html`) | YES (UI only) |
| CLI one-shot | `hermes --oneshot`/`-z` ("single-shot mode, stdout = final response only") | Non-interactive prompt→stdout execution | YES (invocable) but **no run_id/idempotency/event stream/stop**; a separate agent process per call |
| CLI/service management | `hermes gateway {run,status,start,stop,restart,install,uninstall,list,setup,migrate,enroll}` | service lifecycle | YES |
| Messaging gateway | WhatsApp bridge (pid 548360, port 3000, self-chat mode) | human chat channel | YES (connected) |

- **AJ-relevant direct integration surface:** **no AJ↔Hermes task transport/adapter implementation found in AJ** (see §9).

## 8) Actual Hermes functionality (safe verification status)

- **Gateway/runtime liveness:** **VERIFIED (read-only evidence)** — service active, processes running (no current `T`), listeners/socket present (dashboard SPA 200 on 33143, control socket published), heartbeat/state updated, WhatsApp reported connected.
- **Task-submission API (`/v1/runs`) reachable:** **NO — NOT ATTACHED.** Live probe of `127.0.0.1:33143` returned the dashboard SPA for `/v1/health` and `/v1/skills` (HTML, not JSON), and `platforms.api_server` is not enabled in config. The documented task API exists in the product but is **not mounted on this host**.
- **Accept/process a request end-to-end (LLM completion):** **NOT VERIFIED as successful now** — recent logs show provider 402 credit exhaustion/fallback exhaustion for configured OpenRouter/free models; gateway attempts requests but cannot complete successful model responses under current provider/billing state. No safe read-only synthetic task executed.
- **Discover installed skill:** **PARTIAL (structural)** — skill stores/manifests present; runtime discovery path not live-verified.
- **Execute an authorized skill / return structured output / preserve task execution state / recover from worker failure:** **NOT VERIFIED** in this pass (would require executing work/skills or inducing failures; out of read-only/safe scope and currently constrained by provider credits). Existing Hermes session/state/log/DB machinery suggests capability, but not evidenced here.

## 9) AJ–Hermes integration boundary (traced)

- **AJ execution port:** `AJ/aj/execution.py` defines `ExecutionPort` contract and **`UnavailableExecutionAdapter` only** (`name="none"`, `available()=False`, reports `integration_status: NOT ATTACHED`, requires `HERMES GREEN SIGNAL`; `execute` raises `ExecutionUnavailable`). No `HermesExecutionAdapter` implementation present.
- **AJ capability registry/config:** `AJ/config/capabilities.json` declares `hermes.execute_skill` (owner `HERMES`, `execution_adapter: execution_port`, `availability: unavailable`, `verification_status: planned`, note requires GREEN SIGNAL). `AJ/aj/config.py` gates `execution.runtime` (`none|hermes`) and requires `feature_flags.hermes_skills`; defaults to none/disabled. `AJ/aj/runtime.py` reports `attached.hermes: "NOT ATTACHED"`. `aj --check` confirms execution `NOT ATTACHED`.
- **AJ agent/task transport:** `AJ/aj/agents.py` provides JARVIS/HELIX HTTP probe adapters (no agreed task transport); **no Hermes agent adapter, no socket/IPC/HTTP task client to Hermes gateway (33143/gateway.sock)** found in AJ codebase.
- **Tests:** `AJ/tests/test_hermes_contract.py`, `test_orchestrator.py` assert unavailable/not-attached behavior (contract-level, not live runtime integration).
- **Conclusion:** AJ→Hermes boundary is **architecturally reserved but NOT operational/attached**. No reliable submit-task/receive-result path exists in AJ today. Correlation/timeout/retry/cancel/duplicate semantics for Hermes delegation are therefore **unimplemented/unverified** in AJ.

## 10) Security, permissions, and gaps

- Hermes holds configured provider credentials/platform auth (`auth.json`, config, env) — **sensitive; not exposed**. Gateway/service runs as user with broad tool/plugin/skill surface typical of Hermes; AJ must not bypass permission enforcement or auto-execute unreviewed skills.
- AJ lacks attached Hermes adapter/transport and explicit permission/correlation contract for delegated execution.
- Current provider billing/quota exhaustion (402) blocks real LLM-backed completion validation independent of integration wiring.

## 11) Recommended AJ–Hermes boundary (concrete, future/approved work)

**Recommended protocol: the `api_server` platform's durable `/v1/runs` API.** It is the only interface that natively provides what AJ's execution port needs. Mapping (each item is evidenced by the Hermes source read in this pass):

| AJ requirement | Hermes `/v1/runs` mechanism |
|---|---|
| Submit task | `POST /v1/runs` → `run_id` |
| Correlation / task IDs | `run_id` + `X-Hermes-Session-Id` / `X-Hermes-Session-Key` continuity headers |
| Duplicate execution prevention | **Durable idempotency store** `~/.hermes/runs_idempotency.db` keyed by `(scope, idempotency_key)` with request **fingerprint** + persisted status; owner pid/start for orphan detection (`api_server_run_idempotency.py`) |
| Progress / structured output | `GET /v1/runs/{id}` status; `GET /v1/runs/{id}/events` **SSE** (capabilities advertise `run_events_sse`, `tool_progress_events`, `approval_events`) |
| Human/permission gate | `POST /v1/runs/{id}/approval` (+ `clarify`, `resolve-unknown`) — approval stays **inside Hermes**, AJ must not bypass it |
| Cancellation | `POST /v1/runs/{id}/stop` (capability `run_stop`); `steer` for redirection |
| Concurrency backpressure | `gateway.api_server.max_concurrent_runs` (default 10) → `429` past the cap; AJ must treat 429 as retry-after, not failure |
| Auth | `API_SERVER_KEY` (≥16 chars); only `/v1/health` is unauthenticated |
| Skill discovery | `GET /v1/skills`, `GET /v1/toolsets`, `GET /v1/capabilities` |
| Failure propagation | Durable terminal statuses (`TERMINAL_STATUSES`) + SSE error events; restart drain treats interrupted `/v1` runs as failed callers |

**Adapter shape (when approved):** small `HermesExecutionAdapter` implementing the existing `ExecutionPort` in `AJ/aj/execution.py` — submit with an AJ-generated idempotency key, poll/stream status, normalize terminal status → AJ receipt/journal outcome, map 429→retry-after, map timeout→`RECOVERY_REQUIRED` (never blind replay), always surface Hermes approval requirements instead of auto-approving. No Hermes internals imported; no duplication of skill/execution logic in AJ.

**Blocking prerequisites (owner decisions, not engineering gaps):**
1. `platforms.api_server.enabled: true` + ≥16-char `key` in `~/.hermes/config.yaml` (and gateway restart to mount it) — a **configuration/permission change**, explicitly out of scope without the HERMES GREEN SIGNAL.
2. Provider credits/quota (HTTP 402 today) for any end-to-end completion evidence.
3. AJ side: `execution.runtime: "hermes"` + `feature_flags.hermes_skills: true` — deliberately defaulted off.

**Rejected alternatives:** gateway control socket (lifecycle verbs only — no task semantics); dashboard port (UI, not API); `hermes --oneshot` CLI (no run_id/idempotency/SSE/stop; process-per-call, unsuitable as a durable execution boundary — acceptable only as a manual diagnostic).

**No automatic attachment, no config change, no restart, no unreviewed skill execution was performed.**

## 12) Read-only commands/evidence sources (representative)

- `hermes --version/--help`, `hermes gateway --help`
- `systemctl --user status/cat/list-units hermes-gateway.service`
- `ps -eo pid,ppid,stat,etime,cmd` / process tree; `ss -ltnp` (listener 127.0.0.1:33143)
- `~/.hermes/` structure (config/state/logs/sessions/skills/dbs/sockets), `gateway_state.json`, heartbeats, `journalctl --user -u hermes-gateway.service -n 60` (redacted)
- Redacted config structure parse (`config.yaml` keys/sections only)
- AJ integration trace: `AJ/aj/{execution.py,agents.py,config.py,runtime.py}`, `AJ/config/capabilities.json`, `aj --check`
