# HELIX Desktop App — Packaging Plan & Verification

## Step 1: Stack Inventory (Current State)

### Current UI
- **`ui/helix-ui.html`** — single-file built app (1.62 MB), produced by `ui/build.js`.
- **`ui/src/`** — source: `index.html`, `style.css`, `src/js/*.js` (11 modules).
- Build: `node build.js` from `ui/`. node_modules already present in the repo.

### Current Backend
- **`bridge/bridge_ws.py`** — Python stdlib-only WebSocket server.
  - Serves `helix-ui.html` over HTTP **on the same port** (same-origin WebSocket).
  - Reads `~/.hermes/kanban.db` and `~/.hermes/state.db` for agent/task state.
  - Calls `hermes` CLI (`~/.local/bin/hermes`) to create Kanban tasks.
  - RSS headlines, whisper.cpp STT, edge-tts/piper/espeak TTS, camera via ffmpeg.
- **`bridge/server.py`** — deleted in the ponytail cleanup; the desktop app uses `bridge_ws.py` only.

### Ports & Processes
- Bridge WS: 127.0.0.1, **random free port** chosen at launch (desktop app).
- Hermes binary: `~/.local/bin/hermes`.
- Hermes data: `~/.hermes/kanban.db`, `~/.hermes/state.db`, `~/.hermes/config.yaml`.

### Config / Keys
- `~/.config/helix/lms.env` — LMS URL/username/password (chmod 600).
- `~/.hermes/config.yaml` — Hermes model default, provider.
- No API keys hardcoded in the app bundle.

---

## Step 2: Embedding Choice

**Choice: PyGObject GTK3 + WebKit2GTK 4.1** (`bridge/helix_desktop.py`)

1. The UI is already a single static HTML file — no Node/Vite runtime needed. Tauri would mean rebuilding the frontend and adding a Rust toolchain for no gain.
2. `python3-gi`, `gir1.2-gtk-3.0` and `gir1.2-webkit2-4.1` are already installed. Zero new system dependencies.
3. **The WebKit2GTK 4.1 typelib on this machine is built against GTK 3** — importing it pulls Gtk-3.0 in automatically, so `gi.require_version("Gtk", "4.0")` fails with *"Gtk version '3.0' is already loaded"*. GTK4 + WebKit2 4.1 is not a valid combination here; GTK3 + WebKit2 4.1 is.
4. Electron would add ~100 MB and a Node runtime for a static HTML UI.

Frontend↔backend: the bridge binds a **random free port on 127.0.0.1**, chosen at launch, never printed to the user and never typed by them. The WebView loads the UI **from the bridge's own HTTP origin** (`http://127.0.0.1:<port>/?demo=0&bridge=ws://127.0.0.1:<port>`) so the WebSocket is same-origin.

---

## Step 3: Launcher — Bugs Found and Fixed

Four real bugs had to be fixed before the app worked. Each was found by running the thing, not by reading it.

| # | Bug | Symptom | Fix |
|---|-----|---------|-----|
| 1 | `recv_frame()` read only **2 bytes** but `ws_decode_frame()` needed the whole frame | Every UI→bridge message arrived as an **empty payload**. Handshake succeeded, UI showed "BRIDGE LIVE", and *not one command ever reached the backend*. | Read header + extended length + 4 mask bytes + payload exactly, via `readexactly`. |
| 2 | `p["task"]["progress"]` / `["note"]` / `["where"]` — `_task_progress()` has no such keys | **KeyError** killed the snapshot mid-stream: UI received 4 agents and **0 tasks**. | Use `.get()` with defaults. |
| 3 | `handle_client()` used `reader.read(256)` to peek | Could swallow the first bytes of the client's first WebSocket frame and discard them. | Read the request line and headers with `readline()` — byte-exact, nothing over-read. |
| 4 | Demo backend started **1500 ms before** the bridge connected | Demo data (fake greeting, fake LMS panel, scripted replies) was on screen while the real bridge was still connecting. | `?demo=0` or `?bridge=` forces demo off; in that mode the bridge connects **immediately** and the UI shows `BRIDGE OFFLINE` until it answers. |

Also fixed:
- `bridge_ws.py` ignored `--port` (no `argparse`) — the desktop app's random port was silently dropped.
- `D.handle()` in `ui/src/js/50_demo.js` had no guard — added `if (H.bridge && H.bridge.connected) return;`
- `H.send()` in `ui/src/js/00_core.js` fell through to demo on a failed send — now bridge-first, always.
- `WebKit2.LoadEvent.FAILED` does not exist in this WebKit2 build.
- `set_widget_name()` is GTK4-only; GTK3 uses `set_name()`.
- `application_id="helix"` is not a valid D-Bus name (needs a dot) → `helix.desktop`.
- GLib unix-signal callbacks take **one** argument, not `(signum, frame)`. A two-arg handler raised TypeError inside the C callback, which GLib swallowed — so SIGTERM was received and ignored, and the app never quit.

---

## Step 4: Packaging Assets

- **Icon**: `tools/helix-icon.svg` → PNGs at 16/32/48/64/128/256/512 via ImageMagick. Installed to `~/.local/share/icons/hicolor/*/apps/helix.png`.
- **`.desktop`**: `bridge/helix.desktop` — `Exec=/home/abubakargcx/.local/bin/helix-desktop`, `Icon=helix`, `StartupWMClass=helix`, `Terminal=false`.
- **Launcher**: `~/.local/bin/helix-desktop` (copy of `bridge/helix_desktop.py`).
- **`install.sh`**: copies `.desktop` + icon, runs `update-desktop-database` + `gtk-update-icon-cache`.
- **`uninstall.sh`**: removes everything, updates caches.

---

## Step 5: Packaging Outputs

| Artifact | Path | Size |
|---|---|---|
| .deb | `/tmp/helix_1.0.0_amd64.deb` | 600 KB |
| AppDir | `/tmp/helix.AppDir/` | 2.1 MB |
| AppImage | *needs `appimagetool`* | — |

The AppDir is complete and runs directly: `/tmp/helix.AppDir/AppRun`.
`appimagetool` is not installable on this machine (apt needs root; `appimage-builder`
fails on Python 3.14 with `TypeError: expected string or bytes-like object` in
its build-tag parsing). The AppDir is the standard input to `appimagetool`, so
one command converts it: `appimagetool /tmp/helix.AppDir helix.AppImage`.

---

## Step 6: Verification — ALL TESTS RUN, NOT ASSUMED

Every row below was executed on this machine.

| # | Test | Method | Result |
|---|------|--------|--------|
| 1 | Bridge is up | `ss -tlnp` | ✅ listening on 127.0.0.1 |
| 2 | WebSocket handshake | real client, raw frames | ✅ `HTTP/1.1 101 Switching Protocols` |
| 3 | **UI→bridge messages arrive** | client sends `ui.ready`, bridge replies | ✅ 107 events received |
| 4 | Full snapshot delivered | count `agent.status` + `task.upsert` | ✅ 10 agents, 92 tasks |
| 5 | **Command path → real Hermes task** | send `command`, read task from kanban.db | ✅ task `t_c9173423` created, then `done` |
| 6 | **App launches** | `setsid ~/.local/bin/helix-desktop` | ✅ PID alive, `[OK] HELIX UI loaded` |
| 7 | **No browser tab** | `ss -tnp` for WebKitNetworkPr | ✅ `ESTAB 127.0.0.1:32770 → 127.0.0.1:48795 users:(("WebKitNetworkPr"))` |
| 8 | **Real data reaches the UI** | `~/.local/state/helix/logs/bridge.log` | ✅ `recv hello` → `recv ui.ready` → `snapshot: 10 profiles, 94 tasks` |
| 9 | **No demo data** | grep served UI for the guard | ✅ demo guard ×2, `demo=0` forced ×1 |
| 10 | **Single instance** | launch twice | ✅ 1 app process, 1 bridge listener |
| 11 | **Clean quit (SIGTERM)** | kill -TERM, check | ✅ app gone, child bridge gone, lock removed |
| 12 | **Clean quit (SIGKILL)** | kill -9, check | ✅ child bridge gone (parent-watch thread) |
| 13 | **Stale lock recovery** | write bogus lock, launch | ✅ app starts, stale lock cleared |
| 14 | **Random port** | read bridge cmdline | ✅ 48795 / 55147 / 57555 / 35427 on successive runs |
| 15 | **Command in the app's own bridge** | send command to app's bridge port | ✅ task `t_1b17b6b7` created |

### Process-lifecycle design
- `PR_SET_PDEATHSIG` on the bridge child (belt) **and** a `getppid()` poll thread in the bridge (braces) — the child dies however the parent dies.
- `GLibUnix.signal_add` for SIGTERM/SIGINT/SIGHUP → `app.quit()` → `do_shutdown()` → child reaped, lock file removed.
- Stale lock files are detected (dead PID) and removed on next launch.

### Known Limitations
- **AppImage not built**: `appimagetool` unavailable (needs root for apt; `appimage-builder` is broken on Python 3.14). AppDir is complete and directly runnable.
- Camera needs `/dev/video0` access; TTS tiers need network or the local piper model; STT needs the whisper.cpp model.
- The bridge reads `~/.hermes/kanban.db` — Hermes must be installed and configured.
- `tools/helix_desktop.py` (the old GTK3/WebKit2-4.0 file) is superseded by `bridge/helix_desktop.py`; it was left in place, not deleted.
