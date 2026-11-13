# Deleted over-engineering

Audit-driven cleanup. Only dead code / speculative features / backup junk removed.
Correctness paths untouched.

## Deleted files & directories

- `extra/` — patch scripts + 10k-line `temp.py`, never imported anywhere.
- `ui.py.backup.20260925_185638` — 11k-line backup of `ui.py`.
- `main.py.bak`, `main.py.before_groq_fallback` — stale main.py backups.
- `actions/attention_monitor.py.backup`, `actions/attention_monitor.py.before_lazy2`
- `actions/computer_settings.py.backup`
- `actions/desktop.py.backup`
- `actions/send_message.py.backup`, `actions/send_message.py.pre_lazy`
- `actions/youtube_video.py.backup`
- `smart_home_page_new.py` — unused 1400-line page.
- `discord_bot.py` — unused 437-line bot (only a config key referenced it).
- `agent/task_queue.py` — TaskQueue whose worker was never started; orchestrator replaced it.
- `local_voice.py` — unwired 173-line module (main only toggles a flag).
- `actions/operations.py` — dead home-only `FileOperations`, superseded by `file_controller`.
- `actions/screen_processor.py` — no-op stub (vision removed for privacy) + call sites.
- `tools_check_stylesheets.py` — unused.
- `gesture_utils.py`, `tests/test_gesture_utils.py` — unused.
- `wayland_capture.py` — dead stub, never imported.
- `auth/` — empty package (only a docstring).
- generated root audit/report markdown: `FEATURES_AUDIT.md`, `JARVIS_AUDIT.md`, `JARVIS_AUDIT_COMPLETE.md`, `LOCAL_AUTOMATION_AUDIT.md`, `HOLOGRAPHIC_DASHBOARD_RESEARCH_REPORT.md`.

## Deleted code (edits, not whole files)

- `agent/__init__.py` — removed `TaskQueue`, `TaskPriority`, `TaskStatus`, `get_queue` exports.
- `agent/research_agent.py` — removed `DeepResearchAgent`.
- `agent/document_agent.py` — removed `ReportAgent`, `PresentationAgent`, `SpreadsheetAgent`.
- `agent/code_agent.py` — removed `DebugAgent`, `RefactorAgent`.
- `main.py` — removed `screen_process` import, tool declaration, thread block, dispatch branch.
- `agent/executor.py` — removed `screen_process` dispatch branch.
- `agent/planner.py` — removed `screen_process` from tool list.

## Removed dependencies (requirements)

- `google-generativeai` (only `google-genai` is used).
- `opencv-python` (only referenced in disabled screen_processor).
- `mediapipe` (only referenced in disabled screen_processor).
- dedupe `pillow`/`Pillow`.

## Not touched

- `wayland_native.py` shrink (circular import with screen_capture) — deferred; live module.
- `main.py` structural split — deferred; too risky for an audit pass.
- Windows-only deps (`comtypes`, `pycaw`, `win10toast`, `pywinauto`, `pygetwindow`) — guarded imports, kept for Windows.
