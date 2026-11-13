# Bridge

`bridge_ws.py` — the localhost-only WebSocket + HTTP bridge for the Helix UI.
The desktop app (`helix_desktop.py`) starts it on a free loopback port, loads the
UI from it over the same origin, and stops it on exit. The old SSE server
(`bridge/server.py`, port 8787) was deleted.

## Run

    python3 bridge/bridge_ws.py --port 8765
    python3 bridge/bridge_ws.py --selftest     # status rules, no server needed

Desktop app:

    ./install.sh                               # installs ~/.local/bin/helix-desktop
    helix-desktop                              # starts its own bridge + WebView

## Endpoints

The UI connects to `ws://127.0.0.1:<port>` and speaks the protocol documented at
the top of `ui/src/js/00_core.js`. The same port serves HTTP:

| | |
|---|---|
| `GET /` | the built UI (`ui/helix-ui.html`) |
| `POST /tts` | `{text, lang, engine}` → WAV; chain `live-tts → edge-tts → piper → espeak-ng` |
| `POST /stt` | raw `audio/wav` or multipart audio → `{ok, text, lang, ms}` |

## Design notes

- Reads `~/.hermes/kanban.db` read-only. The only profile write is `soul.update`
  (atomic write of the selected profile's `SOUL.md`; unknown agents and empty or
  >64 KB bodies are rejected).
- `download` creates a real `pc` Kanban task; its status is reported honestly
  (`queued`/`running`/`done`), never faked.
- `settings`, `skill.install`, `memory.add/delete`, `vision.source/frame` are not
  wired: the bridge rejects them explicitly, and the UI disables or omits the
  corresponding controls.
- TTS tries live TTS, then edge-tts, then piper, then espeak-ng. If the network is
  unavailable, the local engines still speak.
- Stdlib only, no auth, bound to `127.0.0.1` explicitly. Never widen the bind.
