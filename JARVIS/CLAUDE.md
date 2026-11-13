# CLAUDE.md — Jarvis project status

Persistent context for Claude Code sessions working on this project.

## Project

Jarvis: Linux (Ubuntu) port of a Windows voice assistant ("Brahma Echo"),
using Gemini Live for real-time voice, with cloud/local text-model
fallbacks for planning, memory extraction, and non-voice replies.

## AI provider stack (current)

**Live voice** (`main.py` — `LIVE_MODEL`): Gemini Live only
(`gemini-3.1-flash-live-preview`). Cloud-only, no offline equivalent —
real-time speech in/out requires the Gemini Live websocket API.

**Text-based chat fallback** (`main.py` — `_fallback_reply`,
`_rewrite_reply_text`): **Gemini → Groq → OpenRouter → Ollama (local
qwen2.5:3b)**, in that order. Offline: skips straight to Ollama, checked
via `connectivity.py`'s `is_online()` (DNS-port connectivity probe,
cached 5s).

**Task planning** (`agent/planner.py` — `create_plan`): Gemini → Ollama
(local qwen2.5:3b) → static fallback plan. Groq not yet added here.

**Memory extraction** (`memory/memory_manager.py` — `should_extract_memory`,
`extract_memory`): OpenRouter → Ollama. Groq not yet added here.

## Pending integration

- [x] **Groq** — `groq_client.py` built, mirrors `or_client.py`'s
  interface (`.chat()`, `.chat_json()`, `.vision()`, `.vision_from_file()`,
  `.multi_turn()`). Wired into `main.py`'s main chat fallback chain
  (position: after Gemini, before OpenRouter). **Not yet added** to
  `agent/planner.py` or `memory/memory_manager.py`'s fallback chains.
- [x] **Tavily** — wired into `actions/web_search.py` as the first search
  attempt (before the existing DDG → Gemini chain, which remains intact
  as the fallback tier).
- [x] **Offline mode** — `connectivity.py` added; `main.py`'s chat
  fallback chain checks it and skips cloud providers entirely when
  offline, going straight to local Ollama. Gemini Live (real-time voice)
  itself cannot run offline — it's a cloud websocket API with no local
  equivalent in this codebase. OS-level automation tools (file ops,
  opening apps, computer_control, etc.) already work offline regardless,
  since they don't depend on any LLM call.
- [ ] Groq not yet added to `agent/planner.py` or
  `memory/memory_manager.py` fallback chains (only the main chat reply
  path in `main.py` currently uses it).
- [ ] `google.generativeai` (deprecated) still used in ~10 files —
  migration to `google.genai` not yet done.
- [ ] `ui.py` has two duplicate `class JarvisUI:` definitions (pre-existing
  issue, not introduced by the Linux port) — the first (~1450 lines) is
  dead code, never audited for functionality gaps vs. the active second
  definition.
- [ ] `actions/game_updater.py`'s Epic Games Launcher support reports
  "not installed" on Linux by design (no native Linux Epic client).
- [ ] Browser control: "Chrome is already running without Jarvis remote
  control enabled" — occurs when Chrome was launched outside Playwright's
  control. Not yet fixed.
- [ ] Wayland screenshot/portal capture unreliable (`WaylandCapture portal
  timed out`, gnome-screenshot fallback throws GTK/Gdk errors). Not yet
  fixed.

## Key constraints

- `brahma_connect` package/module names and the `_BRAHMA._tcp.local.` mDNS
  service identifier are intentionally NOT renamed (Android companion app
  pairing protocol depends on them).
- `config/api_keys.json` is gitignored; never commit real keys.
- SQLite connections project-wide must use the `_ClosingConnection` wrapper
  pattern (see `workspace_store.py`, `smart_home/storage.py`,
  `memory/memory_db.py`) — a bare `sqlite3.Connection` used as a context
  manager does NOT close the connection, only commits/rolls back. This
  caused a real file-descriptor-exhaustion crash earlier in the port.
