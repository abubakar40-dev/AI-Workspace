# Helix features added to Jarvis

- `bridge_ws.py` — full Helix WebSocket+HTTP bridge (port 8765): serves `ui.html` at GET /, TTS (live→edge→piper→espeak), STT, kanban task tracking, downloads, soul updates, agent status from ~/.hermes/kanban.db.
- `jarvis_desktop.py` — GTK3+WebKit2 desktop app launching the bridge + embedded UI (adapted from helix_desktop.py).
- `ui.html` — Helix UI (demo backend removed) as primary UI; `ui_src/` source kept.
- `tools/` — Helix tools (lms_client, browser, eras, live_tts, etc.) copied.
- `agents/`, `docs/` — Helix agent profiles and docs copied.
- `main.py` — `_serve_ui_bridge` now runs the full bridge; `_open_ui_html` opens `ui.html` in browser.
- Kept `ui.py` (PyQt) as backend glue; full removal deferred.

## JARVIS -> HELIX hierarchy

JARVIS submits structured requests through `agent_runtime`, which owns a
`HelixManager` in front of the existing `AgentOrchestrator`. HELIX assigns
specialist work, tracks lifecycle states, deduplicates retries, supports
cancellation, and returns a verified report. Specialist agents remain
registered through the existing registry and can be extended without changing
the JARVIS contract.

HELIX's independent voice system is disabled by default with
`HELIX_VOICE_ENABLED=false`. Set it to `true` only when HELIX is intentionally
allowed to own a separate microphone session; this does not change JARVIS's
voice configuration.
