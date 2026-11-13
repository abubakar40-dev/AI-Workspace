# AJ Orb — Claude Web UI (WebKitGTK) Integration Audit

**Date:** 2026-11-11  
**Scope:** Integrate the selected Claude Sonnet 5.5-generated AJ Orb UI (`aj-orb-ui-generation`, preserved untouched) into the real AJ project as a functional desktop capture surface using AJ’s canonical inbox/storage/backend. Continuation from live checkpoint (no restart/rebuild of completed AJ core work).

## Verdict
**IMPLEMENTED / AUTOMATED VERIFIED** for host wiring, UI bundle integration, state mapping, CLI/runtime checks, and AJ regression tests.  
**LIVE DESKTOP VERIFIED:** **NO** (interactive GNOME Wayland acceptance not completed in this session).  
**SMOKE VERIFIED:** partial non-interactive checks only (`aj.orb --check-gui`, system-Python web GUI availability, import/mapping/snapshot checks).  
**MIGRATION:** **NOT PERFORMED** (Home inbox preserved).  
**HOST INTEGRATIONS:** Nautilus/autostart/worker/extension **NOT INSTALLED/ENABLED**.

## What was implemented
- **Reference UI preserved:** `aj-orb-ui-generation/` left untouched.
- **Vendored/integrated UI:** `AJ/orb_ui/` contains copied source/config/build artifacts and integrated changes: `src/aj/bridge.ts`, `src/aj/useAjAdapter.ts`, `src/aj/components/OrbArtwork.tsx` (vector replacement for missing raster orb asset), `App.tsx`, `AjOrb.tsx`, `types.ts`, `OrbBody.tsx`, `ChatCard.tsx`, `index.html`, `index.css` updated for desktop-bridge/transparent host/region reporting/host drop hooks/honest capability handling.
- **Build:** `cd AJ/orb_ui && npm ci --no-audit --no-fund` (95 packages), `npm run build` → **✓ 54 modules**, `dist/index.html` **292.77 kB** (gzip **89.09 kB**) single-file bundle.
- **WebKitGTK desktop host (new):** `AJ/aj/orb_web.py`
  - Runs on system Python with `gi` GTK3 + WebKit2 4.1 + cairo (import-safe when unavailable).
  - Embeds `AJ/orb_ui/dist/index.html` in a transparent, always-on-top, undecorated fullscreen overlay window (XWayland/GDK X11 display compatible path present; Wayland/Mutter behavior still verification-required).
  - Applies dynamic input regions from UI `regions` messages (cairo region input-shape) to reduce desktop obstruction.
  - Bridges UI ↔ backend via `webkit.messageHandlers.aj` (`ready`, `regions`, `position`, `submitDrop`, `captureText`, `pick`, `paste`, `retry`, `clearFinished`, `openInbox`, `openStorage`, `quit`, `log`).
  - Pushes authoritative snapshots from canonical `InboxStore` (`snapshot_state`, `map_record_to_item`) with honest capabilities (`retry` only; no fake pause/cancel/chat/byte-progress).
  - Background worker queue performs canonical capture/process/retry using existing inbox APIs (`capture_file/url/text`, `process_capture`, `retry_failed`), no duplicate inbox/DB/queue/storage.
  - Handles host DnD payloads (`text/uri-list`/file paths/URLs/text), pending drop handoff to UI intent, unsupported/folder feedback, native file picker, clipboard paste, open storage/inbox viewer, quit.
  - Persists orb logical position in per-inbox `index/orb_state.json`; uses per-inbox `orb.lock`; writability preflight and no silent configured fallback.
- **Runtime/CLI wiring:** `AJ/aj/orb.py` now prefers WebKit web host when available and falls back to legacy GTK/Cairo orb (`--gtk` forces legacy); `python -m aj.orb --check-gui` reports `webkit/ui/dist` plus legacy `ok/gtk`. `AJ/aj/__main__.py` `aj orb --check-gui` reports web/legacy availability while preserving JSON shape/exit semantics used by existing checks/tests.
- **Canonical storage/backend preserved:** all captures go through `InboxStore` + existing capture/process/retry APIs and resolved inbox root precedence (explicit arg > `AJ_INBOX_ROOT` > config `core.inbox_root` > `core.data_dir/knowledge-inbox` > legacy home). No second storage.

## Honest capability/status mapping
- Inbox statuses mapped: `incoming|queued -> queued`, `processing -> uploading` (active), `ready|processed -> completed`, `failed -> error`; archived excluded from active UI list.
- `sizeBytes` from record size; `transferredBytes` set to full size only on completion (no fabricated byte progress). `addedAt` from `captured_at`.
- Unsupported/unavailable UI affordances remain honest: pause/cancel/chat disabled by capability flags; clear-finished is UI-side hide of terminal rows (backend archive semantics unchanged).

## Automated verification
- `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **252 passed, 0 failed** (includes existing suites + `tests/test_orb_web_integration.py` [5 tests]).
- Targeted: `tests/test_orb_non_gui.py` (7 passed), `tests/test_orb_web_integration.py` (5 passed), `tests/test_knowledge_inbox.py` + `tests/test_knowledge_inbox_resilience.py` + `tests/test_inbox_subprocess_recovery.py` (15 passed total in targeted run).
- `cd AJ && PYTHONPATH=. .venv/bin/python -m aj --check` → **exit 0**, `ok: true`, Hermes **NOT ATTACHED**.
- `cd AJ && PYTHONPATH=. /usr/bin/python3 -m aj.orb --check-gui` → `{"ok": true, "gtk": true, "webkit": true, "ui": "web", "python": "/usr/bin/python3", "dist": ".../AJ/orb_ui/dist/index.html"}`.
- `cd AJ && PYTHONPATH=. /usr/bin/python3 -m aj orb --check-gui --json` → web UI available.
- `cd AJ && PYTHONPATH=. .venv/bin/python -m aj orb --check-gui --json` → `ok:false, gtk:false, webkit:false, ui:none, exit 5` with clear hint (preserved behavior).
- `cd AJ && PYTHONPATH=. /usr/bin/python3 -c ...` import/mapping/snapshot smoke: `web_gui_available() -> (True, '')`, mapping and snapshot correct on temp `InboxStore`.
- `cd AJ && npm run build` (in `AJ/orb_ui`) → successful single-file build (prior to/consistent with bundled dist).

## Live desktop acceptance (GNOME Wayland) — NOT RUN
**VERIFICATION REQUIRED** for all interactive scenarios on the target session (Ubuntu 26.04.1, GNOME 50.1, Wayland, XWayland/GDK X11 display available): orb visibility/presence across focus changes, app switching, workspace changes, maximized windows, lock/unlock/suspend; actual Nautilus drag-and-drop onto the surface; native file chooser/clipboard paste/URL capture UX; desktop notifications rendering; open-inbox/open-storage behavior; restart/relaunch and position persistence; input pass-through/click regions correctness; CPU/RAM/responsiveness on i5-7300U/8GB/HD 620; screenshots of real running UI. No evidence collected in this session to claim live GNOME acceptance.

## Storage / migration
- Active resolved inbox remains **Home**: `/home/abubakargcx/.local/share/aj/knowledge-inbox` (preserved, **not migrated**).
- Workspace-central storage path requires explicit configuration (`AJ_INBOX_ROOT` or `core.inbox_root`/`core.data_dir`) and approved, quiesced, integrity-checked migration with rollback; workspace mount SQLite WAL suitability for active writes remains **UNVERIFIED** beyond prior smoke.

## Host integrations / approvals
- **Not performed:** Nautilus script installation, autostart enablement, inbox worker service enablement, GNOME Shell extension install, package installs, `sudo`, system/GNOME setting changes, real data migration/cleanup.
- Helper/installer remain prepared (`AJ/scripts/send_to_aj.py`, `AJ/scripts/install_nautilus_send_to_aj.sh`).

## Known limitations / risks
- Wayland/Mutter: transparent fullscreen overlay + input-shape and always-on-top are best-effort and **must be live-verified**; cross-app DnD acceptance can be compositor/session-dependent. X11/XWayland path is available on this session but behavior still needs proof.
- No real byte-progress streaming, pause/cancel per item, or chat backend in current AJ inbox — UI intentionally does not expose these as functional.
- `clearFinished` hides rows in UI only (not archival); archived backend records are excluded from snapshot.
- Long-run WebKitGTK memory/CPU behavior on target hardware **UNVERIFIED**.
- Optional extractors/network conditions affect rich URL/file extraction as before.

## Files changed/added (key)
- Added: `AJ/aj/orb_web.py`, `AJ/tests/test_orb_web_integration.py`, `engineering/audits/2026-11-11-aj-orb-web-ui-integration.md`
- Modified: `AJ/aj/orb.py`, `AJ/aj/__main__.py`
- Integrated UI (vendored, under AJ): `AJ/orb_ui/src/*` (bridge/adapter/artwork/hooks), `AJ/orb_ui/dist/index.html`, `AJ/orb_ui/package-lock.json`/node_modules via install (build artifacts)
- Preserved: `aj-orb-ui-generation/`, prior backups and Home inbox data

## Next required steps
1. Run live GNOME Wayland desktop acceptance matrix and capture evidence/screenshots; fix any compositor/input-region/DnD issues found.
2. If approved, install/verify Nautilus "Send to AJ Inbox" and re-test file-manager capture flow.
3. If approved, perform safe quiesced Home→workspace inbox migration with integrity verification and rollback retention.
4. Consider GNOME Shell extension/hybrid IPC only if floating/panel surface fails acceptance (requires approval/implementation).