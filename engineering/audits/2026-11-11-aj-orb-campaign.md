# AJ Orb Campaign Audit — 2026-11-11

**Scope:** AJ Orb subsystem + minimum supporting AJ interfaces (`aj/orb.py`, `aj/inbox.py`, `aj/inbox_cli.py`, `aj/__main__.py`, `aj/runtime.py`, helpers/scripts, tests, docs).  
**Mode:** Inspect → implement → test → document (no restart of completed AJ core work).  
**Host:** Ubuntu (GNOME Wayland session env observed: `XDG_SESSION_TYPE=wayland`, `WAYLAND_DISPLAY=wayland-0`, `DISPLAY=:0`), Python 3.14.4, Dell Latitude 5480 class constraints respected (lightweight Cairo/procedural rendering, bounded worker, no heavy runtime).

## 0) Baseline and preservation

- **Pre-change backup (verified):** `backups/orb_campaign_20261111T082401Z/` contains `AJ/aj`, `AJ/tests`, `AJ/integrations`, `AJ/scripts`, `AJ/pyproject.toml`, `engineering_snapshot`.
- **Baseline checks:** `aj --check` exit 0 (Hermes NOT ATTACHED). Targeted inbox tests 10 passed. GTK available in system Python (`/usr/bin/python3`, `gi`/Gtk 3.0 ready); unavailable in AJ `.venv` (`No module named 'gi'`). No running Orb process found at inspection time.
- **Existing data preserved:** `/home/abubakargcx/.local/share/aj/knowledge-inbox` (~88K, sqlite/originals/extracted/metadata/index/orb_state present) untouched; no migration/deletion performed.

## 1) Root-cause diagnosis (reported issues)

| Reported issue | Root cause (evidence) | Status after campaign | Evidence |
|---|---|---|---|
| Tiny plain dark circle with "AJ" | Old `aj/orb.py` drew a 64x64 dark circle + text via Cairo with no state visuals/identity system. | **Implemented (design changed)**; visual quality **VERIFICATION REQUIRED** on live desktop | Code rewrite in `AJ/aj/orb.py` (luminous layered core, state rings/indicators, hover/press/drag-over/paused/processing/error visuals, lightweight animation) |
| Appears fixed / not properly movable | Orb supported drag-move and persisted position in inbox state, but restore/clamping/monitor recovery were minimal; UX unclear. | **Implemented**; multi-monitor/scaling/restart behavior **VERIFICATION REQUIRED** | `_save_position`, `_restore_position`, `_clamp_to_monitor`, persisted `orb_state.json`; unit-level state roundtrip tests |
| Disappears/minimizes when clicking other windows/file manager | Likely GNOME Wayland/Mutter handling of window hints/focus for `UTILITY`+`keep_above` app window (not conclusively proven from terminal; no Shell.Eval). Old code had no focus-loss hide handler. | **Partially mitigated by hints, not proven solved** | New hints: `keep_above`, `stick`, `DOCK`/`UTILITY` fallback, skip taskbar/pager; no hide-on-focus-out logic. **VERIFICATION REQUIRED / potentially BLOCKED by compositor** |
| Dragging files onto it practically impossible | Depends on visibility/focus/stacking and Wayland cross-app DnD acceptance; old DnD handling existed but limited feedback and folder handling. | **Partially addressed**; live Nautilus→Orb DnD **VERIFICATION REQUIRED** | Multi-URI parsing, file/URL/text handling, folder/unsupported explicit feedback, drag-over visual state, async enqueue; Nautilus "Send to AJ" fallback prepared |
| Intended features not working / controls unclear | Orb had limited menu/actions and synchronous processing in worker thread; CLI `orb` not registered (`aj orb --help` failed baseline). | **Implemented** (core controls/backend paths wired); live GUI behavior **VERIFICATION REQUIRED** | `aj orb` command added, menu actions: capture files, paste, process pending, retry failed, pause/resume, open viewer/folder, refresh/summary/copy path, recent activity, quit; async worker/events/notifications |
| Storage created under Home instead of central AI workspace | `inbox.default_data_dir()`/Orb resolved to `~/.local/share/aj/knowledge-inbox` by default; `core.data_dir` effective default is home; no canonical `core.inbox_root`/`AJ_INBOX_ROOT` precedence in store. | **Implemented (canonical resolution + no silent configured fallback)**; migration to workspace **not performed** | `resolve_inbox_root`, config/env-aware `InboxStore`, CLI/Orb use resolved root, writability preflight, explicit `--inbox-root`/`AJ_INBOX_ROOT`; existing Home data preserved |
| Visual identity unsatisfactory | Plain prototype UI. | **Implemented**; subjective/desktop polish **VERIFICATION REQUIRED** | Cairo procedural redesign with layered core/glow cues, state colors/rings, compact 72px orb |
| Expected fully working feature | Multiple integration/runtime gaps. | **PARTIALLY COMPLETE** | See feature matrix and verification limits below |

## 2) Architecture decisions

- **Reuse canonical inbox:** Orb uses `InboxStore` and existing capture/process/retry/summary/list APIs; no duplicate queue/database/processing engine. (CURRENT DIRECTION, implemented)
- **GTK runtime separation without venv mutation:** `aj orb` runs in current interpreter when GTK available, else falls back to system Python (`/usr/bin/python3 -m aj.orb`) with AJ `PYTHONPATH` and explicit inbox root. No PyGObject install into venv, no project Python change. (CURRENT DIRECTION, implemented)
- **Storage precedence:** explicit arg > `AJ_INBOX_ROOT` > `config.core.inbox_root` > `config.core.data_dir/knowledge-inbox` > legacy home default. Explicit root behavior preserved for tests. (CURRENT DIRECTION, implemented)
- **Async UI:** background worker + main-loop event drain for capture/process feedback; bounded queue; no main-thread extraction/fetch. (IMPLEMENTED)
- **Wayland reliability:** best-effort GTK hints; acknowledge Mutter limitations honestly; provide Nautilus send script, clipboard, file chooser, CLI/worker as fallbacks. No unsupported claims. (VERIFICATION REQUIRED for desktop behavior)

## 3) Feature status

| Feature | Previous state | New state | Evidence / notes |
|---|---|---|---|
| Floating window | Basic GTK window | Redesigned frameless orb window with hints + position persistence | `AJ/aj/orb.py`; live always-visible behavior **VERIFICATION REQUIRED** |
| Window persistence (position/state) | Partial (saved state) | Save/restore/clamp, paused mode persisted, single-instance lock per inbox | `index/orb_state.json`, flock lock; unit tests for state/lock |
| Drag-and-drop | Basic URI/text handling | Multi-URI, file/URL/text, folder/unsupported feedback, drag-over visual, async enqueue | Code inspection + helper tests; Nautilus cross-app **VERIFICATION REQUIRED** |
| Multiple files | Limited | Each drop URI processed independently with per-item result events/counts | Worker event model; **VERIFICATION REQUIRED** end-to-end on desktop |
| URL capture | Inbox supported, Orb basic | Orb routes URL/text-URI captures through canonical store; status feedback | Reuses `capture_url`; network extraction depends on env/deps |
| Clipboard capture | Basic text | Paste action + text/file-URI handling path; user feedback | Menu action `paste`; desktop clipboard behavior **VERIFICATION REQUIRED** |
| Inbox integration | Shared store concept but path/UX gaps | Canonical config-aware shared store/root resolution; process/retry/summary/list/open viewer/folder | `aj/inbox.py`, `aj/orb.py`, CLI checks; inbox tests green |
| Pause/resume | UI toggle existed | Pause blocks new capture jobs in worker (queued in-memory until resume) and shows state; resume releases | Implemented; semantics documented (not durable pre-accept queue) |
| Notifications | notify-send best effort | Event-driven notifications (batched/single result, errors, status) | Best-effort; desktop rendering **VERIFICATION REQUIRED** |
| Summary | Basic | Live summary in menu/tooltip/status from canonical inbox | `InboxStore.summary()` |
| Storage | Home-default, inconsistent | Canonical resolution + writability preflight + explicit root/config/env support; no silent configured fallback | `resolve_inbox_root`/tests; Home data preserved, no migration performed |
| CLI launch | Missing `aj orb` | `aj orb` top-level + `python -m aj.orb`, help/check-gui/system-python/inbox-root options | `aj --help`, `aj orb --help`, tests, `aj --check` CLI list |
| Restart persistence | Position/state partial | Orb state persisted/restored; captures durable in inbox store | Existing inbox durability + orb state tests; full desktop restart **VERIFICATION REQUIRED** |

## 4) Storage

- **Previous actual path (effective/default):** `~/.local/share/aj/knowledge-inbox` (real data present, preserved).
- **Canonical path policy now:** explicit/config/env/data_dir-driven via `resolve_inbox_root`; workspace path can be set explicitly. No silent Home fallback for configured/unavailable storage.
- **Migration:** **not performed** (requires stop/copy/integrity/reopen/approval). Existing Home inbox retained intact.
- **Writability:** Orb preflight writes a probe file in inbox index dir and fails clearly on permission/mount issues.

## 5) Files changed/added

- **Modified:** `AJ/aj/orb.py` (rewrite), `AJ/aj/inbox.py` (canonical resolution/config-aware store), `AJ/aj/inbox_cli.py` (canonical default store resolution), `AJ/aj/__main__.py` (orb command + GTK fallback launch), `AJ/aj/runtime.py` (CLI check includes `orb`,`inbox`), `AJ/aj/orb_autostart.py` (smarter autostart Exec), `AJ/scripts/send_to_aj.py`, `AJ/scripts/install_nautilus_send_to_aj.sh`, `engineering/IMPLEMENTATION_STATUS.md`, `engineering/KNOWN_ISSUES.md`, `engineering/DECISIONS.md`.
- **Added:** `AJ/tests/test_orb_non_gui.py`, `AJ/docs/10_AJ_ORB.md`, `engineering/audits/2026-11-11-aj-orb-campaign.md`, backup `backups/orb_campaign_20261111T082401Z/`.
- **Not changed by campaign:** JARVIS/HELIX/Hermes runtime attachments, existing inbox DB data, host autostart/Nautilus/systemd installation, venv packages.

## 6) Testing

| Category | Command | Result |
|---|---|---|
| Syntax | `cd AJ && PYTHONPATH=. .venv/bin/python -m py_compile aj/inbox.py aj/inbox_cli.py aj/orb.py aj/orb_autostart.py aj/__main__.py aj/runtime.py` | **PASS** (exit 0) |
| Inbox regression (targeted) | `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_knowledge_inbox.py tests/test_knowledge_inbox_resilience.py tests/test_inbox_subprocess_recovery.py` | **10 passed** |
| New Orb non-GUI tests | `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_orb_non_gui.py` | **7 passed** |
| Full AJ regression | `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` | **247 passed, 0 failed** |
| AJ check | `cd AJ && PYTHONPATH=. .venv/bin/python -m aj --check` | **exit 0, ok true** (Hermes NOT ATTACHED) |
| System GTK probe | `cd AJ && PYTHONPATH=. /usr/bin/python3 -m aj.orb --check-gui` | **PASS** (`{"ok": true, "gtk": true, "python": "/usr/bin/python3"}`) |
| Venv GTK probe | `cd AJ && PYTHONPATH=. .venv/bin/python -m aj orb --check-gui --json` | **Expected unavailable** (exit 5, clear hint; venv lacks gi) |
| Orb/inbox CLI help | `python -m aj orb --help`, `python -m aj inbox orb --help` | **PASS** |

**Not run / cannot prove here:** interactive GNOME Wayland tests (focus/stacking, Nautilus drag-drop, maximized/workspace behavior, lock/unlock, scaling/monitor changes, notifications UI, long-run idle CPU/memory, actual file capture from desktop). No host-level installs performed.

## 7) Remaining issues

- **VERIFICATION REQUIRED:** live desktop behavior on GNOME Wayland (visibility, drag-drop across apps, menu usability, notifications, multi-monitor/scaling, long session).
- **PARTIALLY IMPLEMENTED:** always-accessible overlay semantics may be constrained by Mutter; Nautilus send helper exists but not installed/enabled by this campaign.
- **BLOCKED (pending approval/action):** host-level Nautilus/autostart/systemd installation, migration of existing Home inbox to workspace mount with stop/copy/verify, and any missing native GTK packaging changes (not needed on inspected host).
- **Known semantic note:** pause holds new capture jobs in-memory until resume (UI-level pause) rather than durably accepting-and-deferring processing; review if stricter durability is required.

## 8) Honest verdict

**PARTIALLY COMPLETE.** Core Orb architecture, CLI integration, canonical storage resolution, GTK-via-system-Python launch strategy, redesigned UI/async capture controls, and automated regressions are implemented and green (247 passed, `aj --check` exit 0). Real GNOME Wayland desktop interaction (especially no-disappear behavior and Nautilus drag-drop) is not fully provable in this environment and requires live user validation.


## 2026-11-11 continuation (post-campaign smoke fixes)
- **Critical GUI render defect fixed (VERIFIED):** smoke launch via `/usr/bin/python3 -m aj.orb` revealed repeated draw exceptions `AttributeError: 'cairo.Context' object has no attribute 'RadialGradient'` (pycairo API misuse) causing broken rendering. Fixed in `AJ/aj/orb.py` to use `cairo.RadialGradient` / compatible fallback. Subsequent 3s smoke run (`/usr/bin/timeout 3s /usr/bin/python3 -m aj.orb --inbox-root /tmp/... --debug`) exited on timeout (124) with no draw tracebacks; orb state/lock/db files created.
- **Config/env regression fixed (VERIFIED):** `AJ_INBOX_ROOT` was parsed by strict env-to-config mapping as unknown section `inbox_root`, breaking `aj --check` and canonical inbox CLI capture when set. `AJ/aj/config.py` now excludes `AJ_INBOX_ROOT` from config-section merging (consumed directly by inbox resolution). Verified: `AJ_INBOX_ROOT=... aj --check` exit 0; `AJ_INBOX_ROOT=... scripts/send_to_aj.py <file>` captured successfully (summary shows ready item in env-selected inbox).
- **Orb UX additions:** added "Capture URL..." dialog and "Storage & config info..." menu action in `AJ/aj/orb.py`.
- **Regression:** `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **247 passed, 0 failed** after fixes.
