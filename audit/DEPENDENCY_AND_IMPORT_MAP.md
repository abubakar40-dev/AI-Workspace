# Dependency and Import Map

## 1. Why this exists

The cleanup rule was "do not delete a module before tracing its dependencies". This is the
trace that authorised the removals — including two modules I initially removed and had to
put back because a caller existed.

## 2. JARVIS import graph (functional edges only)

```
main.py
├── actions/*          (25 tool implementations, imported as modules)
├── agent/planner.py   PLANNER_PROMPT, plan()
├── agent/executor.py  _call_tool()          ← NEW: core.policy, core.audit
├── agent_runtime      start(), subscribe()
├── dashboard.server   DashboardServer
├── bridge_ws          (started by the dashboard)
├── command_center     CommandCenter (UI)
├── plugin_manager     PluginManager
├── workspace_store    store
├── core.prompt.txt    PROMPT_PATH
└── [REMOVED] brahma_connect.service, smart_home.service

agent/executor.py → actions/* + core.policy + core.audit
bridge_ws.py      → tools/lms_client.py        ← path was broken, now fixed
dashboard/server  → bridge_ws, workspace_store
actions/file_controller.py → (share: link | folder | email)   [device path removed]
```

`core/` imports nothing from the application. That is what lets `bridge_ws.py` and the
HELIX tools import `core.voice` without an import cycle.

## 3. Edges that made the removal possible (or blocked it)

| Edge | Direction | Consequence |
|---|---|---|
| `main.py` → `brahma_connect.service` | import at module load | Had to remove import **and** the init block **and** the port-in-use branch |
| `main.py` → 6 `actions.brahma_connect` functions | function import | Every one had to be removed from declarations *and* both dispatch chains |
| `actions/file_controller.py` → `actions.brahma_connect` | **lazy import inside `share_file`** | Would have survived as a runtime `ImportError` caught by a broad `except` and reported as "Device sharing unavailable". Removed explicitly. |
| `main.py` → `smart_home.service` | import + init | Removed with the redirect block that consumed it |
| `main.py` → `smart_home.smart_device_manager` | **lazy import inside every utterance** | This ran before normal dispatch on *every* request. Removed. |
| `command_center.set_brahma_connect_service` | method only, no import | Kept: it is a no-op setter, still referenced by `tests/test_command_center.py` |
| `workspace_store.py:102` | comment only | Kept |
| `helix/tools/helix-call-server.py` → `helix_voice` | **import at call time** | **Blocked deletion.** File was restored and repointed at the shared contract. |
| `helix/bridge/bridge_ws.py:59` → `tools/live_tts.py` | subprocess path | **Blocked deletion.** Restored and repointed. |

The last two are the reason the instruction "trace dependencies before deleting" matters:
both files looked like duplicates, and both had live callers in a *different* directory.

## 4. External dependencies by consumer

| Package | Consumers | Still needed |
|---|---|---|
| `google-genai` | JARVIS voice, HELIX transports | ✔ |
| `websockets` | `bridge_ws.py`, `live_server.py` | ✔ |
| `playwright` | browser automation | ✔ (not importable from the system interpreter — see §6) |
| `requests`, `beautifulsoup4` | research, LMS client | ✔ |
| `cryptography` | Brahma pairing **and** other secret storage | ✔ (Brahma gone, storage remains) |
| `python-kasa` | smart-home only | ✘ **removed** |
| `edge-tts` | TTS fallback | ✔ |
| `customtkinter` / Qt | UI | ✔ |

## 5. HELIX import graph

```
tools/helix-call-server.py → tools/helix_voice.py → core.voice (JARVIS)
tools/live_server.py       → core.voice (JARVIS)   [hard requirement]
tools/live_tts.py          → core.voice (JARVIS)
bridge/bridge_ws.py        → tools/live_tts.py (subprocess), tools/eras.py
ui/ (Vite)                 → gods-eye-view/ (upstream), bridge/
```

Path resolution is `JARVIS_ROOT` (env) or `../../JARVIS` relative to the file, so the
sibling layout is what makes it work. If HELIX is ever deployed without JARVIS beside it,
`JARVIS_ROOT` must be set — and `live_server.py` will say so instead of starting wrong.

## 6. Broken imports found

| # | Where | Was | Now |
|---|---|---|---|
| D-1 | `JARVIS/bridge_ws.py:302` | `os.path.join(dirname, "..", "tools")` — one level *above* the repo | `os.path.join(dirname, "tools")` |
| D-2 | `JARVIS/actions/file_controller.py` | lazy `from actions.brahma_connect import connect_execute` | removed with the device-share branch |
| D-3 | `helix/tools/live_server.py` | self-contained config | imports `core.voice`, hard-fails if absent |
| D-4 | `helix/tools/check-live.py:19` | `gemini-3.8-live` | `gemini-3.1-flash-live-preview` |

## 7. Environment findings

- JARVIS is running **Python 3.14.4**; `README` claims 3.11/3.12. This matters: libraries
  such as RealtimeSTT declare `Python <3.13`, so they are **not** installable here.
- `playwright` is **not importable** from the system interpreter, only from `venv/`. Any
  script that shells out to `python3` for browser work will fail.
- `requirements.txt` is **unpinned**. A fresh install today can produce a different stack
  from the one the tests pass on.

## 8. Module → feature classification

| Module group | Classification |
|---|---|
| `core/` | Necessary infrastructure (new) |
| `agent/`, `agents/` | Approved capability — orchestration |
| `actions/` | Approved capabilities — tools |
| `bridge_ws.py`, `dashboard/` | Necessary infrastructure — remote control |
| `memory/`, `workspace_store.py` | Approved capability — memory |
| `error_logger.py`, `config/` | Necessary infrastructure |
| `actions/attention_monitor.py` | Approved capability — proactive alerts |
| `tools/lms_client.py` | Deferred capability — LMS (kept, not wired) |
| `plugins/`, `plugin_manager.py` | Extension point, keep |
| `gui/`, `ui_src/`, `assets/` | UI, keep |
| `bin/`, `scripts/` | Development/support |
| `docs/` | Documentation |
| `tests/` | Test support |
