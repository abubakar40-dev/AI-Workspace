# AJ Orb — Final Acceptance Audit (continuation, 2026-11-11)

## Verdict
**PARTIALLY COMPLETE** (implementation and automated/integration checks improved; critical live GNOME Wayland desktop acceptance, host integrations, and real storage migration remain unverified/unapproved).

## Baseline and environment (verified)
- Workspace: `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`, AJ project present, non-git. Backup preserved: `backups/orb_campaign_20261111T082401Z/`.
- OS/Desktop: Ubuntu 26.04.1, GNOME Shell 50.1, session `XDG_SESSION_TYPE=wayland`, `WAYLAND_DISPLAY=wayland-0`, `DISPLAY=:0` (GDK probe reported `X11Display`), Nautilus 50.2.2.
- Hardware target context: Dell Latitude 5480, i5-7300U, 8 GB RAM, Intel HD 620 (design kept lightweight; no formal perf profiling).
- Runtimes/tools: `/usr/bin/python3` 3.14.4 with `gi` GTK3 3.24 ready; GTK4/Adw libs and GJS 1.88.0 installed system-wide; AJ `.venv` lacks `gi`; no PySide6/PyQt6. `gdbus`, `notify-send`, `wmctrl`, `gio` available; portals active. `libgtk-layer-shell0` installed but GNOME Mutter does not support wlr-layer-shell.
- AJ baseline: `247 passed, 0 failed` (`cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q`), `aj --check` exit 0, Hermes NOT ATTACHED.
- Storage (actual resolved, no overrides): `core.data_dir=/home/abubakargcx/.local/share/aj`, `core.inbox_root=null`, resolved inbox `~/.local/share/aj/knowledge-inbox` (existing real data preserved: sqlite + 1 captured item + orb_state). No workspace inbox dir under `AJ/data` by default.

## Root causes (confirmed/inferred)
- **Render crash (CONFIRMED, fixed):** `AJ/aj/orb.py` used invalid pycairo call `cr.RadialGradient(...)` causing repeated draw exceptions; fixed to `cairo.RadialGradient`/fallback. Smoke launch now renders without draw tracebacks.
- **Config/env regression (CONFIRMED, fixed):** `AJ_INBOX_ROOT` became unknown config section via strict env mapping, breaking `aj`/`aj inbox` when set; `AJ/aj/config.py` now excludes it from section merge (read directly by inbox resolution). Verified with `aj --check` and env-root capture.
- **False-success in file-manager helper (CONFIRMED, fixed):** `scripts/send_to_aj.py` previously could report success for missing paths because `aj inbox capture <path>` may treat non-file positional as text; helper now validates local file/URI intent, uses explicit `--file/--url/--text`, parses JSON status, and reports truthful per-item failures (missing file correctly reported failed).
- **Storage centralization gap (CONFIRMED):** defaults resolve to Home; canonical precedence implemented (`explicit > AJ_INBOX_ROOT > core.inbox_root > core.data_dir/knowledge-inbox > legacy home`) with no silent configured fallback and writability preflight, but active data not migrated to `/run/media/abubakargcx/My Drive/AI_WORKSPACE/AJ/...`.
- **GNOME Wayland accessibility/DnD (INFERRED/PLATFORM-CONSTRAINED, UNVERIFIED):** ordinary GTK windows rely on Mutter hints for stacking/visibility and cross-app DnD; best-effort hints implemented, but reliable always-accessible drop-target behavior on GNOME Wayland cannot be guaranteed from code/tests alone.

## Architecture decision
- **Selected (CURRENT DIRECTION):** GTK3/Cairo orb front-end (`aj/orb.py`) launched via current interpreter or system Python GTK fallback + canonical `InboxStore` backend; reliable capture complements via `aj inbox` CLI, `scripts/send_to_aj.py`, and prepared Nautilus Scripts integration (user-approved install). No duplicate inbox/queue.
- **Evaluated/rejected for now:** wlr-layer-shell on GNOME Mutter (unsupported target), PySide6/PyQt6 (not installed; no evidence of bypassing Mutter; rewrite/install cost), GTK4/Libadwaita migration (libs present but no proven accessibility advantage, migration cost), XWayland as guaranteed fix (unproven). 
- **Promising but not implemented/installed:** GNOME Shell extension (GJS 1.88 / Shell 50.1 present) as shell-native always-accessible surface with thin IPC to AJ backend — requires separate approved implementation/install and compatibility care; **BACKLOG/BLOCKED pending approval**.

## Implemented/updated this continuation
- `AJ/aj/orb.py`: Cairo render fix, URL capture dialog, storage/config info action, menu/status improvements (earlier rewrite retained: async worker, DnD/clipboard/file chooser, pause/resume/process/retry/viewer/folder/summary/recent, position/state/lock, writability preflight).
- `AJ/aj/config.py`: `AJ_INBOX_ROOT` excluded from strict env config-section merge.
- `AJ/scripts/send_to_aj.py`: truthful JSON/per-item validation and reporting (file/URI/URL/text), explicit CLI flags, missing-file/folder detection.
- `AJ/scripts/install_nautilus_send_to_aj.sh`: idempotent install/uninstall/dry-run, batched invocation.
- Docs/audits/status/decisions/known-issues updated.

## Verification evidence (exact outcomes)
- `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **247 passed, 0 failed**.
- `cd AJ && PYTHONPATH=. .venv/bin/python -m aj --check` → **exit 0, ok true**, Hermes NOT ATTACHED.
- `cd AJ && PYTHONPATH=. /usr/bin/python3 -m aj.orb --check-gui` → `{"ok": true, "gtk": true, "python": "/usr/bin/python3"}`.
- `cd AJ && /usr/bin/timeout 3s /usr/bin/python3 -m aj.orb --inbox-root /tmp/... --debug` → exit 124 (timeout), no draw tracebacks, created `index/inbox.sqlite3`, `index/orb_state.json`, `index/orb.lock`.
- `AJ_INBOX_ROOT=/tmp/x .venv/bin/python -m aj --check` → exit 0, ok true.
- `send_to_aj.py --json <missing>` → `{"ok": false, "captured": 0, "failed": 1, ...}` (truthful). Multi-file real capture to temp `AJ_INBOX_ROOT` → captured 2, inbox summary `ready: 2` in selected root. URL and `--text` captures routed correctly to canonical inbox in temp roots.
- `bash scripts/install_nautilus_send_to_aj.sh --dry-run` → reports target/actions without installing.

## Desktop acceptance (GNOME Wayland)
**LIVE DESKTOP VERIFIED:** none of the interactive critical scenarios (orb remains accessible on focus/app switch, Nautilus drag-drop onto orb, notifications rendering, workspace/maximize/lock/unlock/suspend/monitor scaling, long-run GUI stability, native screenshots). **VERIFICATION REQUIRED.**

## Storage migration
- Home inbox `~/.local/share/aj/knowledge-inbox` preserved (not moved/deleted). No copy/migration to workspace performed. Destination mount/writability and SQLite WAL suitability on My Drive **UNVERIFIED**. Safe migration requires approved stop/backup/copy/integrity/reopen procedure.

## Remaining limitations / blockers
- Live GNOME Wayland orb accessibility and direct DnD acceptance unproven (possible Mutter limitation). 
- Host installs not performed (Nautilus script, autostart, worker service, any extension). 
- Real data migration not performed. 
- Pause semantics hold new capture jobs in-memory until resume. 
- Optional extractors/network conditions may affect URL/rich-file extraction outcomes.

## Required approvals
- Install/uninstall Nautilus script in `~/.local/share/nautilus/scripts`.
- Enable autostart entry and/or user worker service.
- Implement/install GNOME Shell extension (if chosen).
- Perform verified copy/migration of real Home inbox data to workspace and any later cleanup (original must remain until verified).
- Install any system packages (none required for current path).
