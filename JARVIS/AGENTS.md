# AGENTS.md — Jarvis handoff notes

## Objective
Provide a summary of the conversation for another agent to continue work on the codebase or conversation.

## Requirements
- (none)

## Decisions
- `actions/file_controller.py` was extended in place (not rewritten), so every
  pre-existing public function keeps its name, signature defaults and message
  strings: `list_files`, `create_file`, `create_folder`, `delete_file`,
  `move_file`, `copy_file`, `rename_file`, `read_file`, `write_file`,
  `find_files`, `get_largest_files`, `get_disk_usage`, `organize_desktop`,
  `organize_folder`, `get_file_info`, `file_controller`. New parameters were
  only ever *appended* with defaults that reproduce old behaviour.
- No path allow-list/sandbox was added. Scope is the whole machine (all
  drives, all user homes, `/root`, hidden/system folders); the only limits are
  OS permissions, and permission-blocked operations escalate via `sudo -n`
  then `pkexec` (`elevated=false` opts out, explicit `elevated=true` forces
  the GUI password prompt).
- Recycle-bin stays the default for `delete`; permanent removal only happens
  with `permanent=true`. Elevated deletes move the item into the *user's* bin
  (files/ + info/*.trashinfo) so they stay restorable instead of `rm -rf`-ing.
- Sharing supports four methods: `device` (Brahma Connect `send_file`),
  `link` (temporary tokenised LAN HTTP server, default 30 min), `folder`
  (copy into `~/Shared`), `email` (`xdg-email --attach`). Folders are zipped
  before a link is generated.
- Relative paths resolve against module state `_STATE["cwd"]`, initialised to
  `Path.cwd()` at import — identical to the old `Path(raw).expanduser()`
  behaviour at startup, so nothing that worked before changed meaning.

## Work State
### Completed
- `actions/file_controller.py`: full file-manager layer added —
  navigation (`cd`/`pwd`/`up`/`tree`, paged `list`), any-format `read`
  (PDF via pdftotext→pypdf, DOCX/PPTX/XLSX, image metadata, ffprobe/PyAV
  media info, archive listings, binary hex dumps), binary `write`
  (`base64_encoded`), elevation helpers (`_elevate`, `_elevate_shell`,
  `_elevated_trash`), permission-tolerant `_walk` + system-wide `find`,
  `recent`, `chmod`/`chown`/`permissions`/`info` (owner, mode, MIME, SHA-256),
  `users`, `partitions`, `trash` (list/empty/restore), `archive`/`extract`,
  `open`/`open_with`/`reveal`, `share`/`shares`/`unshare`, `describe`
  (delegates to `file_processor`), `capabilities`, plus an action-alias map
  (`ls`, `cat`, `mkdir`, `rm`, `mv`, `cp`, `search`, `du`, `stat`, `zip`,
  `unzip`, `drives`, …).
- `main.py` `TOOL_DECLARATIONS["file_controller"]`: description + 42 properties
  (verified JSON-serialisable via `ast.literal_eval`; all 15 legacy actions
  still advertised).
- `agent/planner.py` `PLANNER_PROMPT`: file_controller block expanded with the
  new actions/params and notes on any-format reads, sharing and escalation.
- `core/prompt.txt`: added the "full file manager over the whole computer"
  instruction incl. `elevated=true` retry guidance.
- `tests/test_file_controller.py`: 48 tests (path resolution, CRUD, formats,
  navigation, search, permissions, trash via monkeypatched `_trash_dir`,
  share link over loopback, archives, system info, legacy behaviour, aliases).
- Verification: 58/58 repo tests pass for touched code; standalone smoke run
  exercised 80+ behaviours including a real elevated write to `/root`.

### Active
- None.

### Blocked
- Leftover probe file from testing: `/root/jarvis_elevated_probe.txt`. It was
  created by an elevated write test and could not be removed afterwards
  because `pkexec` auth timed out. Remove with
  `sudo rm -f /root/jarvis_elevated_probe.txt`.
- `pytest` lives in `.venv` (`pip install pytest`); run the suite with the
  venv python.

### Active
- **Obsidian Integration**: Full Obsidian vault integration complete.
  - `obsidian_integration.py` — Vault manager (conversations, memory, search, migration)
  - `migrate_to_obsidian.py` — Migrates SQLite + chat_history → Obsidian vault
  - `install_obsidian.sh` — Helper script for Obsidian installation
  - `OBSIDIAN_SETUP.md` — Setup guide
  - Vault at `~/.obsidian-vault/` with 165+ entries (10 conversations, 155 memory files)
  - Dual-write: `update_memory()` writes to BOTH SQLite AND Obsidian
  - `main.py` `_build_config()` includes vault context in LLM system prompt
  - `main.py` `_on_text_command()` logs every conversation to Obsidian
  - Original SQLite database preserved at `memory/personal_memory.sqlite3`
  - 148 memory entries + 9 conversation files migrated from SQLite/chat_history
  - Vault context (~6000 chars) sent to LLM for both online and offline modes
  - Voice mode switching: "switch to offline mode" → Ollama + local TTS + Obsidian
  - "switch to online mode" → Gemini Live

### Active
- **Wayland screenshots + full desktop input (Task 4)**: built and
  live-verified; one idle-pointer check outstanding.
  - `screen_capture.py` — the capture chain: portal silent → portal
    interactive (GNOME capture UI auto-confirmed by injecting Enter over
    uinput; `JARVIS_SCREENSHOT_MANUAL=1` = a human clicks instead) → grim →
    gnome-screenshot → X11 grab (X11 sessions only; always rejected on
    Wayland). Uniform/black frames are never reported as success; a wedged
    `xdg-desktop-portal` is restarted once and the call retried once.
    Signature `capture(dest=None, timeout=20.0) -> (ok, detail)` keeps both
    callers working (`computer_control` passes a path, tests call it bare).
  - `portal_shot_client.py` — one-shot GLib portal client, JSON on stdout;
    runs under system `/usr/bin/python3` (the venv lacks PyGObject).
  - `desktop_input.py` + `setup_uinput.sh` — uinput backend (rules applied:
    `/etc/udev/rules.d/99-jarvis-uinput.rules`, `/dev/uinput` rw-rw-rw-).
    Keyboard injection live-proven (volume 82 % → 100 % → restored to 82 %),
    BTN_LEFT click live-proven (ButtonPress/ButtonRelease in `xev`);
    pointer-motion delta check still pending an idle pointer.
  - `wayland_native.py` (your module) now tries the chain first and keeps
    scrot/grim only as fallback. **Correction of the old note below: scrot
    does NOT work here** — it exits 0 but writes a 100 % black PNG (XWayland
    cannot read the Wayland desktop), `mss` is black too, grim has no
    wlr-screencopy on GNOME, gnome-screenshot hangs/denies. The intermediate
    `screen_capture` that simply delegated to scrot was replaced (its
    `capture()` also raised TypeError against `computer_control`'s call).
  - `actions/meeting_assistant.py` and `ui.py` were left untouched (still
    importing `wayland_native`) and get real captures through the chain.
  - Tests: `tests/test_screen_capture_chain.py` (32, fully mocked),
    `tests/test_desktop_input.py`, `tests/test_computer_control_wiring.py`,
    plus the existing `tests/test_screen_capture.py` — suite: **328 passed,
    0 failed** (the earlier "311/312, test_verify failing" note was stale).

### Active
- **Multi-Agent System (Task 6)**: Full multi-agent architecture implemented and live-tested.
  - `agent/agent_base.py` — BaseAgent, AgentRegistry, AgentTask, AgentResult, AgentStatus, AgentType
  - `agent/research_agent.py` — ResearchAgent, DeepResearchAgent (web search, fact synthesis, report compilation)
  - `agent/document_agent.py` — DocumentAgent, ReportAgent, PresentationAgent, SpreadsheetAgent (PDF, DOCX, PPTX, XLSX)
  - `agent/code_agent.py` — CodeAgent, DebugAgent, RefactorAgent (coding, debugging, refactoring)
  - `agent/orchestrator.py` — AgentOrchestrator: decomposes goals, manages dependencies, coordinates agents
  - `agent/supervisor.py` — Supervisor (CEO): real-time monitoring, progress reporting, stats dashboard
  - `agent/__init__.py` — Unified exports, version 2.0.0
  - Dependency management: agents wait for prerequisites, share data via context
  - Live test verified: "Research Python async patterns and create summary report" → ResearchAgent (4 steps) → DocumentAgent (1 step) → Orchestration completed
  - Test suite: 529 passed, 6 pre-existing failures

### Active
- **Error Logger System**: Automatic error/crash logging to `~/.jarvis/errors.md`.
  - `error_logger.py` — Global error logger: log_error, read_errors, get_error_summary, format_errors_for_report, resolve_error
  - `~/.jarvis/errors.md` — All errors stored chronologically with date, time, type, message, context, stack trace, status (open/resolved)
  - `agent/error_handler.py` — Auto-logs errors from analyze_error via `_log_to_error_logger`
  - `agent/executor.py` — Auto-logs tool execution errors via try-except in `_call_tool`
  - `main.py` — Error commands added to JarvisLive:
    - `show_errors` / `view errors` / `list errors` — Show recent errors
    - `error summary` / `error stats` / `error report` — Show error statistics
    - `show error ERR-XXXX` / `view error ERR-XXXX` — Show specific error by ID
    - `clear errors` / `clear error log` — Clear error log (backup with timestamp)
  - JARVIS reads and reports errors on demand
  - Every agent/command failure auto-logged

## Next Move
1. Remove the leftover `/root/jarvis_elevated_probe.txt` when a password can
   be supplied.
2. **Task 5 = Local voice mode testing** (backlog item 2): `pip install
   faster-whisper`, `apt install espeak-ng`, confirm `local_voice.py`
   standalone, then wire the voice-triggered mode switch.
3. Optional: wire `share`'s `device` method into a live Brahma Connect test —
   only the code path was exercised, not a real paired device.

## Relevant Files
- `screen_capture.py`: the screenshot chain (Task 4).
- `portal_shot_client.py`: one-shot XDG portal client (GLib, system python3).
- `desktop_input.py` / `setup_uinput.sh`: uinput keyboard+mouse backend and
  its udev setup.
- `wayland_native.py`: capture module used by `meeting_assistant.py` and
  `ui.py`; delegates to the chain first, scrot/grim fallback.
- `actions/file_controller.py`: the file-manager implementation.
- `main.py` (~line 428 `TOOL_DECLARATIONS`, ~line 2175 dispatch): tool schema
  and Gemini function dispatch (`file_controller(parameters=args, player=self.ui)`).
- `agent/planner.py`: multi-step planner prompt listing the tool's actions.
- `agent/executor.py`: `_call_tool` also routes `file_controller`.
- `core/prompt.txt`: system prompt guidance.
- `tests/test_file_controller.py`: regression suite for this feature.
- `actions/file_processor.py`: used by the `describe` action for AI analysis.
- `actions/brahma_connect.py`: `connect_execute` `send_file` used by
  `share method=device`.

## Important Context
- Backups `main.py.bak` and `main.py.before_groq_fallback` were deliberately
  not touched.
- `actions/computer_control.py` and `actions/file_processor.py` show as
  modified in git but are pre-existing user edits from before this session.
- Repo tests: `.venv/bin/python -m pytest tests -q` (venv python is required;
  system `python3` lacks `send2trash`).
