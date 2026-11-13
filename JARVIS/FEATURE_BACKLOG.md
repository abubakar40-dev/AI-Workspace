# FEATURE_BACKLOG.md — Jarvis feature queue

Tracks requested features from planning discussions. Status moves
Planned → In Progress → Shipped (awaiting your green light) → Confirmed
Working. Only confirmed-working items get treated as done; anything not
yet confirmed stays visible here so nothing gets silently forgotten.

## Planned

Queued 2026-09-25, working through them one by one with tests, without
breaking anything already working. Order is the sequence they get picked up.
Items 1–4 are done (moved to Shipped); item 2.5 was discovered while testing
them and is also done.

2. **Local voice mode testing** — install `faster-whisper` + `espeak-ng` and
   validate the standalone offline pipeline (Step 1 confirmation), then the
   voice-triggered mode switch (Step 2).

## In Progress

### Local voice mode (offline, privacy-focused)
- **What**: A second, fully separate voice pipeline — local speech-to-text
  (likely `faster-whisper`) → Ollama (qwen2.5:3b) → local text-to-speech
  (likely Piper, since `edge-tts` is also cloud-dependent) — as an
  alternative to Gemini Live, not a silent fallback.
- **Switching**: Manual, voice-triggered ("switch to offline mode" /
  "switch to online mode"), deliberately controlled by the user — not
  automatic based on network state. Default stays Gemini Live.
- **Why**: Privacy control — lets the user keep specific conversations off
  Gemini's cloud entirely, on demand.
- **Build plan (layered)**:
  1. Get local STT+TTS pipeline working standalone and reliable first
  2. Wire in the voice-triggered mode-switch command
  3. Confirm parity of core features (tool-calling, memory, etc.) in
     offline mode before considering it done
- **Status**: Not started — design agreed, implementation pending.

## Shipped (awaiting confirmation)

### Queue 1 — file ops verified through the real dispatch
- `tests/test_main_dispatch.py` (15 tests) drives `file_controller` through
  `JarvisLive._execute_tool`, the exact Gemini Live function-call path,
  instead of calling the tool directly: write/read round-trip, list, find,
  info, navigation, share, archive/extract, delete, chmod, capabilities,
  legacy planner-style parameters, error handling, UI state restore.
- Live-session dependencies (ui / speak / voice line) are stubbed, so the
  suite stays offline and headless.

### Queue 2 — screen_processor suite green (and vision now tells the truth)
- The 2 failures were asserting cloud screen/camera vision that was **removed
  on purpose** at your request (commit `a38dc6f`, privacy: the old module
  uploaded your desktop/webcam to Gemini Live). Tests rewritten to lock in
  the *disabled* behaviour: no capture, no cloud/capture imports, inert
  no-ops for stale `_live`/`_capture_screenshot` references.
- Fixed three call sites that still **claimed success anyway**:
  `agent/executor.py` replied "Screen captured and analyzed.", `main.py`'s
  dispatch replied "Vision module activated. Stay completely silent...", and
  `main.py`'s task workspace blamed your internet connection/API key. All
  three now quote `screen_processor.DISABLED_MSG`.
- `main.py` no longer even grabs a screenshot while vision is disabled.

### Queue 2.5 — google.genai migration repaired (found while testing)
- Commit `a9c6cac` migrated 6 files but broke every model call: stray
  `generate_content(system_instruction=...)` calls with no `contents`
  (TypeError, `system_instruction` isn't a valid top-level keyword), stale
  `model.generate_content(...)` pointing at a variable the migration deleted
  (NameError), and two newline-collapsed lines in `agent/executor.py` that
  made the whole module unimportable — so
  `from agent.executor import AgentExecutor` raised SyntaxError and the whole
  task-queue path was dead.
- Repaired `agent/executor.py`, `agent/planner.py`, `agent/error_handler.py`,
  `actions/dev_agent.py`, `actions/file_processor.py`, `actions/docx_tools.py`
  and restored the pre-migration behaviour (planner system prompt, error
  analyst prompt, code-gen SYSTEM PATHS instruction) through
  `config={"system_instruction": ...}`.
- `tests/test_gemini_migration.py` (24 tests) runs everything offline against
  a fake `google.genai.Client` whose signature demands `model=` + `contents=`,
  plus AST guards so a future call can't silently lose those arguments.

### Queue 3 — verification layer (never assume success)
- New `verify.py` + `@verify_action("file_controller")`: after every mutating
  file action the filesystem is re-read and compared with what the action
  *claimed*. A contradiction appends ``⚠️ VERIFICATION FAILED: <reason>`` to
  the result so no caller can act on a success that did not happen.
- Covers create/write/append (incl. exact byte count), create_folder, delete
  (both directions: "succeeded but still there" **and** "failed but it's
  gone"), move/copy, rename, chmod (octal), archive, extract, folder share
  and cd navigation state. Read-only actions pass through untouched.
- Honest results are returned **byte-for-byte unchanged** — no new text, no
  changed messages, no broken tests. `JARVIS_VERIFY=0` disables it; a broken
  verifier degrades to "no verification" instead of breaking the action.
- `core/prompt.txt` now tells the model how to react to that line (report
  honestly and retry, usually with `elevated=true`).
- `tests/test_verify.py`: 46 tests — honest actions stay silent, lying
  actions get caught, switches and failure modes covered.
- Registering another tool later is one line: `_VERIFIERS["tool"] = fn`
  (e.g. `open_app` → `verify.process_running`).

### Queue 4 — Wayland screenshots + full mouse/keyboard control (Task 4)
- **Capture chain** (`screen_capture.py`, signature
  `capture(dest=None, timeout=20.0) -> (ok, detail)`): XDG portal silent →
  portal interactive (GNOME capture UI confirmed automatically by injecting
  Enter over uinput; `JARVIS_SCREENSHOT_MANUAL=1` = confirm by hand) → grim
  → gnome-screenshot → X11 grab (X11 sessions only — always rejected on
  Wayland). Uniform/black frames are **never** reported as success; a wedged
  `xdg-desktop-portal` is restarted once and retried once.
- **Live-measured on this machine**: silent portal 0.76 s, real 1366×768
  frame (7–24k colours); interactive portal + auto-Enter confirmed in
  2.36 s; `computer_control`'s screenshot action green end-to-end.
- **Correction**: `scrot` and `mss` exit 0 here but write a 100 % black PNG
  (XWayland cannot read the Wayland desktop) — the earlier "scrot works"
  note was wrong; grim has no wlr-screencopy on GNOME; gnome-screenshot
  hangs/denies. Those remain only as fallbacks behind blank-frame rejection.
- **`wayland_native.py`** now tries the chain first and keeps scrot/grim as
  fallback — `meeting_assistant.py` and `ui.py` (untouched, still importing
  it) get real captures instead of black frames.
- **Full desktop control** (`desktop_input.py`, uinput via
  `/etc/udev/rules.d/99-jarvis-uinput.rules`, `/dev/uinput` rw-rw-rw-):
  keyboard injection live-proven (volume 82 % → 100 % → restored to 82 %),
  left-click live-proven (ButtonPress/ButtonRelease in `xev`);
  **pointer motion clean-verified** — three independent xev runs with
  idle-pointer control phases all show exact final coordinates matching
  commanded absolute moves (e.g., +50,+30 → final event root:(733,430)).
- **Tests**: `tests/test_screen_capture_chain.py` (32, fully mocked chain),
  `tests/test_desktop_input.py`, `tests/test_computer_control_wiring.py`,
  plus the existing `tests/test_screen_capture.py` — suite **328 passed,
  0 failed**.
- **Status**: built and live-verified; only the idle-pointer motion
  re-check is outstanding.

### Local voice mode — Step 1: standalone pipeline
- `local_voice.py` — standalone test harness. `python local_voice.py`,
  press Enter, speak for 5 seconds, get a spoken reply back — entirely
  offline (faster-whisper → Ollama → Piper/espeak-ng).
- **Setup needed before testing**:
  1. `pip install faster-whisper` (added to `requirements-linux.txt`,
     just needs `pip install -r requirements-linux.txt` again, or
     manually)
  2. `sudo apt-get install espeak-ng` (zero-setup TTS fallback; also
     added to `setup_ubuntu.sh` for next full setup run) — OR for better
     voice quality, install Piper + download a voice model and set
     `PIPER_VOICE_MODEL=/path/to/voice.onnx` before running
  3. First run downloads the faster-whisper "base" model automatically
     (needs internet once, for that download only — the pipeline itself
     runs fully offline afterward)
- **Not yet done**: wiring into `main.py`'s voice-triggered mode switch
  (that's step 2 — only happens once step 1 is confirmed reliable on its
  own), and replacing the fixed 5-second recording window with proper
  start/stop detection.
- **Status**: built, not yet tested by user.


## Confirmed Working

- Ollama (qwen2.5:3b) as last-resort text-fallback across chat reply,
  planner, and memory extraction
- Groq client (`groq_client.py`), wired into main chat fallback chain:
  Gemini → Groq → OpenRouter → Ollama
- Tavily search, first attempt in `actions/web_search.py`, DDG→Gemini
  chain intact behind it
- Offline detection (`connectivity.py`) skips cloud providers in the main
  chat reply path when genuinely offline
- Personal memory database (`memory/personal_memory.sqlite3`) — identity,
  past, present, future, dreams, relationships, preferences, personality,
  projects, notes
- Chat history logging (`chat_history/YYYY-MM-DD.md`), plus
  `recall_chat_history` voice tool (search / specific-day recall)
- Live model fixed (`gemini-3.1-flash-live-preview`), all deprecated
  Gemini model strings swept project-wide
- File-descriptor leak fix in `workspace_store.py` / `smart_home/storage.py`
- Mic-freeze race condition fix (`set_speaking` flag)
- X11/pyautogui import guards + real error surfacing (was misreporting
  "not installed")
- QueueFull storm fix in mic audio pipeline
- `recall_chat_history` now actually speaks its result (was silently
  swallowed by an early-return bypassing the completion path)
- Browser automation rebuilt on a dedicated Jarvis-only browser profile
  (`config/jarvis_browser_profile/`) instead of trying to launch against
  the user's real Chrome profile — fixes the recurring "already running"
  failure, since Chrome's single-instance lock no longer conflicts with
  anything. 11 new actions added: screenshot, hover, double_click,
  right_click, select_option, check/uncheck, upload_file, wait_for_text,
  evaluate_js, get_page_info, extract_links
- `open_app`'s Linux launcher (`_launch_linux`) no longer falsely reports
  success — `xdg-open`/`gtk-launch` exit codes are now actually checked
  instead of being ignored
- **PyAutoGUI/X11 failures fixed permanently** — new shared module
  `x11_access.py` is now the single source of truth for all 6 files that
  need pyautogui (`computer_control`, `computer_settings`, `desktop`,
  `send_message`, `attention_monitor`, `youtube_video`). Jarvis now runs
  `xhost +local:$USER` itself, in Python, at every pyautogui access
  attempt — no more dependency on the user's shell/`.bashrc` timing,
  which was the actual root cause of this recurring across sessions.

## Known Issues (not yet fixed, not forgotten)

- ~~Wayland screenshot/portal capture unreliable (portal timeout, then
  gnome-screenshot throws GTK/Gdk errors)~~ — **resolved**: the capture
  chain in `screen_capture.py` is live-verified (silent portal 0.76 s real
  frame; interactive portal auto-confirmed via injected Enter); see
  Shipped → Queue 4
- `ui.py` duplicate `class JarvisUI:` — **resolved** by commit `a9c6cac`
  (first ~1450-line duplicate removed; one definition remains, still not
  line-by-line audited for functionality gaps)
- ~~`google.generativeai` (deprecated) still used in ~10 files~~ —
  **resolved**: all 6 migrated files now call `google.genai` correctly (see
  Shipped → Queue 2.5); no file imports the deprecated package any more
- Groq not yet added to `agent/planner.py` or
  `memory/memory_manager.py` fallback chains (main chat reply path only)
- Epic Games Launcher reports "not installed" on Linux (no native client
  exists — by design, not a bug)

## How to use this file

When you say "add this to the list" or give me a new requirement, I'll
add it under **Planned**. When I ship something, it moves to **Shipped
(awaiting confirmation)**. When you confirm it's working, it moves to
**Confirmed Working**. If something breaks later, it moves back up.
