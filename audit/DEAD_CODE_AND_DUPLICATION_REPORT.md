# Dead Code and Duplication Report

Every removal below was dependency-traced first. Counts are measured, not estimated.

---

## 1. Removed: Brahma / Android

| Item | Files | Lines | Evidence it was safe |
|---|---|---|---|
| `brahma_connect/` (gateway, pairing, discovery, crypto) | 28 | 1,426 | sole importer was `main.py` + `file_controller` lazy import |
| `actions/brahma_connect.py` (6 tool functions) | 1 | ~90 | imported only by `main.py` |
| 6 tool declarations in `main.py` | — | ~105 | declared but the feature had **no paired device** |
| `_handle_brahma_connect_command` (voice handler) | — | ~137 | called before normal dispatch on every utterance |
| `_connect_tool_voice` (result narrator) | — | ~38 | only fed the removed tools |
| Connect init block in `main()` | — | ~42 | started a gateway on a port |
| `config/brahma_connect.json`, `config/brahma_connect/` | 2+ | — | device records → `backup/`, not deleted |
| `tests/test_brahma_connect*.py` | 2 | 229 | tested only the removed package |
| device branch inside `file_controller.share_file` | — | ~28 | would have raised ImportError at runtime |
| `JARVIS/tools/{live_server,helix_voice,eras,helix-call-*}.py` + assets | 17 | 1,995 | no JARVIS importer; `eras.py` byte-identical to HELIX's |

**Total: ~48 files, ~4,090 lines.**

## 2. Removed: smart home

| Item | Files | Lines |
|---|---|---|
| `smart_home/` (service, manager, storage, providers, base) | 12 | 1,588 |
| `smart_home_control` declaration | — | ~13 |
| dispatch branch | — | ~4 |
| `_handle_smart_home_command` | — | ~52 |
| per-utterance redirect block in the voice path | — | ~10 |
| `self._smart_home = SmartHomeService()` | — | 1 |
| `config/smart_home.sqlite3`, `smart_home.key` | 2 | → `backup/` |
| `python-kasa` from both requirement files | — | 1 line × 2 |

**Total: 14 files, ~1,668 lines.**

The redirect is worth calling out: it ran `SmartDeviceManager()` and
`self._smart_home.list_devices()` **before every normal request**, with zero devices
configured. Every utterance paid that cost.

## 3. Removed: HELIX's independent voice configuration

| Before | After |
|---|---|
| 3 model-id defaults (`gemini-3.8-live`), differing from JARVIS's `gemini-3.1-flash-live-preview` | 1 (`core.voice.LIVE_MODEL`) |
| 3 API-key parsers | 1 (`core.voice.read_gemini_key`) |
| 2 persona blocks (live_server, helix_voice) | 1 shared persona + per-transport rider |
| hard-coded 16000 / 24000 | `core.voice.SEND/RECEIVE_SAMPLE_RATE` |

No file was deleted for this. The three transports were kept because each has a live caller
(`helix-live.service`, the bridge `/tts` chain, `helix-call-server.py`). What made them a
second *core* — independent configuration — is gone.

## 4. Consolidated: duplicate repositories

| Duplicate | Size | Action |
|---|---|---|
| `JARVIS/JARVIS/` (nested clone, same commit `cffa32d`) | 1.5 G | → `backup/JARVIS-nested-duplicate-20261106/` |
| `HERMES/` (same commit as `.hermes/hermes-agent`) | 6.3 G | → `backup/HERMES-workspace-duplicate-20261106/` |

## 5. Duplication that remains (deliberately)

| Duplication | Why it stays | Suggested resolution |
|---|---|---|
| `live_tts.py` in both `JARVIS/tools/` and `helix/tools/` | Each bridge launches its own repo-relative copy. Deleting either breaks that bridge. | Extract a `voicetts` package both import once one transport is retired |
| Two tool-dispatch chains in `main.py` + `agent/executor.py` | Structural; the live chain is a 3,600-line async method | Add the policy guard to chain A, then converge |
| `helix/bridge/bridge_ws.py` vs `JARVIS/bridge_ws.py` | ~90% identical (TTS chain, Hermes DB paths, log dir) | One shared module with a project-specific UI file |
| Hermes memory/task/messaging vs JARVIS's own | Hermes is a separate runtime | Route through one owner; do not merge stores |
| `helix/docs/PROGRESS.md` (3,600+ lines) vs `docs/*` | History vs reference | Archive PROGRESS into `docs/history/` |

## 6. Dead code that remains (found, not removed)

| Item | Where | Why not removed |
|---|---|---|
| `_is_port_in_use` | `main.py` | may still be used by the dashboard path; needs a caller check |
| `command_center.set_brahma_connect_service` | `command_center.py:804` | no-op setter, still named by `tests/test_command_center.py` |
| `command_center._brahma_connect_service` | `command_center.py:171` | same |
| `workspace_store.py:102` comment referencing `smart_home/storage.py` | `workspace_store.py` | comment only; no behaviour |
| Dashboard upload dirs named "Brahma Uploads" | `dashboard/server.py` | cosmetic naming; renaming changes a user-visible path |
| `tools/check-office-match.py`, `check-webgl.py`, `shot-url.py` | JARVIS | diagnostics, possibly still used by hand |
| `tools/vps-preflight.sh`, `check-oci-retry.sh` | JARVIS | deployment scripts, may be in use |

These are logged rather than deleted because "no importer found by grep" is not proof of
"unused" for scripts and UI strings.

## 7. Was line count reduced for its own sake?

No. Two of the removals were features the owner had already retired (Android, smart home);
one was a genuine duplicate tree; one was a byte-identical file copy. Nothing that a live
code path called was removed. The one case where a removal *would* have broken something —
`helix_voice.py`, imported by `helix-call-server.py`, and `live_tts.py`, launched by two
bridges — was caught by the reference check and reverted.
