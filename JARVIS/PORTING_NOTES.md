# Jarvis — Linux Port Notes (from Brahma Echo)

This is a working port of the Windows-only Brahma Echo codebase to Ubuntu Linux,
rebranded as Jarvis. Read this before you launch it — it tells you exactly what
was fixed, what's stubbed, and what still needs your decision.

## 1. Setup

```bash
cd JARVIS
bash setup_ubuntu.sh          # installs apt deps + creates .venv + pip installs
nano config/api_keys.json     # paste in your real API keys
source .venv/bin/activate
python main.py
```

`config/api_keys.json` already has `"os_system": "linux"` set, so the app will
**skip the Windows-oriented onboarding wizard** and boot straight in — as long
as you fill in at least `gemini_api_key` (the app's primary LLM). Gemini has
a free tier (`gemini-2.5-flash` via AI Studio, aistudio.google.com/app/apikey) —
worth using if you don't want to burn OpenRouter credits for everyday use.

## 2. Fixed (crash-level bugs — these would stop the app from starting at all)

- **`actions/attention_monitor.py`** — top-level `import ctypes; from ctypes import wintypes`
  ran unconditionally and would crash Python immediately on Linux, before the app
  even started. Now guarded. Window-title scraping now uses `wmctrl` on Linux;
  TTS playback now uses `ffplay`/`paplay`/`mpg123`/`aplay` (whichever is installed)
  instead of the Windows MCI API.
- **`actions/game_updater.py`** — same problem with top-level `import winreg`.
  Now guarded. Steam detection now checks real Linux install paths
  (`~/.steam/steam`, `~/.local/share/Steam`, Flatpak). Process detection uses
  `psutil`/`pgrep` instead of `tasklist`. Scheduled update runs now use `crontab`
  instead of `schtasks`.
- **`actions/reminder.py`** — was 100% Windows Task Scheduler. Rewritten with a
  parallel Linux path: uses the `at` daemon if available, otherwise a detached
  background process, firing `notify-send` + a sound when due.
- **`actions/dev_agent.py`** — fixed a real bug: `subprocess.Popen([...], shell=True)`
  with a list argument silently drops all arguments after the first on Linux
  (POSIX shell=True quirk). This was breaking "open in VS Code" — VS Code would've
  opened with no folder. Fixed to only use `shell=True` for Windows `.cmd` files.

## 3. Rebranding (Brahma Echo/Brahma AI → Jarvis)

Renamed across ~60 files: wake word, window titles, class names (`BrahmaUI` →
`JarvisUI`, `BrahmaLive` → `JarvisLive`), tool names (`shutdown_brahma` →
`shutdown_jarvis`), logo assets (`Brahma_Lite_Logo.png/ico` → `Jarvis_Logo.png/ico`),
log messages, and generated-content templates (e.g. website builder footer text).

**Deliberately NOT renamed:** the `brahma_connect` Python package, the
`config/brahma_connect.json` file, and the `_BRAHMA._tcp.local.` mDNS service
identifier used by the pairing/discovery protocol. This is the subsystem that
talks to the **Brahma Connect Android companion app** (which I removed from this
copy since you only asked for the desktop Linux port — it's a separate Gradle
project). If you rename the protocol identifier here without also updating the
Android app, pairing breaks. Say the word if you want me to rename this too and
walk through updating the Android app to match.

A handful of purely internal, never-user-visible names still say "Brahma"
(variable names like `brahma_text`, PDF style names like `brahma_h1`, a folder
name `~/Desktop/BrahmaProjects`, an AES salt constant). None of these affect
behavior or are visible in the UI — I left them to avoid unnecessary risk of
typos in a huge file. Happy to do a full sweep if you want zero occurrences.

## 4. Found but NOT fixed — needs your input

**`ui.py` has two complete `class JarvisUI:` definitions** (originally
`BrahmaUI`), at line ~9848 and line ~11309. In Python, the second definition
silently overwrites the first — so ~1,450 lines of the first copy are dead code
that never runs. This is **pre-existing** in the original Brahma Echo codebase,
not something the port introduced. It's not a crash risk (the app runs fine off
the second definition), but it means:
- The file is carrying ~1,450 lines of inert code.
- If the first (dead) copy has any method or fix that the second copy is
  missing, that functionality is silently absent from the running app.

I did not attempt to merge them — that needs careful line-by-line comparison to
avoid breaking something. Want me to do that audit next?

## 5. API keys — current state

- **Gemini**: already fully wired (main LLM). Has a free tier.
- **OpenRouter**: already fully wired, and **already includes Nemotron models**
  (`nvidia/nemotron-3-super-120b-a12b:free` and others) in `or_client.py`'s
  model list — this matches the OpenRouter key you said you have.
- **Groq**: **not integrated at all** in the current codebase. I added a
  placeholder field in `config/api_keys.json`, but no code calls it yet. This
  is new integration work, not a port — say if you want it added (e.g. as a
  fast fallback model in `or_client.py`, or wired into `main.py`'s reply chain).
- **Tavily**: same — **not integrated**. Current web search
  (`actions/web_search.py`) uses DuckDuckGo + Gemini's search tool. Adding
  Tavily as a dedicated search backend is new work, not a port.

## 6. Known functional limitations on Linux (by design, not bugs)

- **Epic Games Launcher features** report "not installed" on Linux — there's no
  native Linux Epic client (only via Heroic/Proton, which isn't handled here).
- **Steam GUI-automation** (auto-clicking through install dialogs to pick a
  drive letter) is a Windows-only concept — on Linux, `install`/`update` actions
  launch Steam via `steam://` URIs correctly, but you'll need to click through
  Steam's own dialog manually (no drive-letter concept on Linux anyway).
- **`attention_monitor.py`'s toast-notification reading** (the feature that
  detects incoming calls/messages by reading Windows' notification database)
  has no direct Linux equivalent and is inert on Linux — it checks for the
  Windows notification DB path, doesn't find it, and safely no-ops. Window-title
  based detection (via `wmctrl`) still works for apps that are simply open on
  screen.
- **Windows Task Scheduler shortcuts, registry-based startup, dark-mode
  toggling via registry, volume control via pycaw** — all guarded and replaced
  with Linux equivalents already present in the original code (`systemctl`,
  `gsettings`, `pactl`/`wpctl`), no changes needed there.

## 7. What I have NOT been able to test

I don't have a display, audio devices, camera, or mic in my sandbox, so none of
this has actually been launched. Every fix above is verified by (a) reading the
code path carefully and (b) `python3 -m py_compile` across the entire tree
(passes clean). Real runtime testing has to happen on your machine — please
run `python main.py` and send me the actual traceback if anything errors; that
will be much faster to fix than me guessing blind.

## 8. Files changed/added vs. original

- Rewrote: `actions/attention_monitor.py`, `actions/game_updater.py`,
  `actions/reminder.py`, `actions/dev_agent.py` (partial)
- Renamed: `assets/Brahma_Lite_Logo.{png,ico}` → `assets/Jarvis_Logo.{png,ico}`
- Added: `config/api_keys.json`, `requirements-linux.txt`, `setup_ubuntu.sh`,
  this file
- Removed: `brahma-connect-android/` (separate Android project, out of scope),
  `.venv`, `.git`, `__pycache__`
