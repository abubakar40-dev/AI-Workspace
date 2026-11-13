# DECISIONS.md

## 2026-11-10 (continuation)
- **Checkpoint/live evidence over stale reports:** AJ suite is 200/200 (not historical 180/193 claims from old reports); `BATCH_2_FINAL_ENGINEERING_REPORT.md` preserved but treated as stale.
- **Phase 2 orb implementation:** GTK3+PyGObject via system Python, frameless/lightweight always-on-top draggable orb; no heavy UI runtime introduced; import-safe without GTK. Orb shares inbox capture/process code paths.
- **Inbox storage/ownership:** AJ-owned local inbox under `~/.local/share/aj/knowledge-inbox/` (configurable), SQLite WAL index, originals/metadata/derived separated; originals never replaced by summaries/extractions. Best-effort extractors with graceful degradation; Instagram handled conservatively (URL preserved + explicit limited-extraction note).
- **Hardening scope:** Added viewer/worker/CLI/autostart helpers, resilience + subprocess restart-visibility tests, and integration helper artifacts (Nautilus script installer, systemd user worker template) without broad refactors.
- **Audit honesty:** Phase 1 remains OPERATIONALLY GREEN but STRICT SPEC COVERAGE = VERIFICATION REQUIRED; crash matrix (1–16, A–F) mapped with proven/partial/unproven status. Hermes/AJ/JARVIS/HELIX integration and HELIX runtime remain verification-required pending evidence.
- **Safety/identity:** No destructive cleanup, no Docker/local-LLM production architecture, no JARVIS voice test weakening; JARVIS and HELIX remain separate identities.


## 2026-11-11 AJ Orb campaign
- **Orb architecture (CURRENT DIRECTION):** keep Orb as a GTK3/Cairo desktop front-end to the canonical AJ Inbox (`InboxStore`), not a separate capture/store/queue system. Redesigned UI with async worker/event feedback and bounded lightweight rendering for constrained hardware.
- **GTK runtime strategy (CURRENT DIRECTION):** do not install PyGObject into AJ venv or change project Python env. `aj orb` uses current interpreter if GTK available, otherwise falls back to system Python with AJ source on `PYTHONPATH` and explicit resolved inbox root. Same canonical logic/storage.
- **Canonical inbox storage resolution (CURRENT DIRECTION):** precedence explicit arg > `AJ_INBOX_ROOT` > `config.core.inbox_root` > `config.core.data_dir/knowledge-inbox` > legacy home `~/.local/share/aj/knowledge-inbox`. Explicit `InboxStore(root)` preserved for compatibility. No silent Home fallback when configured/explicit storage is unavailable; Orb performs writability preflight. Existing Home inbox data preserved; migration to workspace is a separate approved, verified operation.
- **GNOME Wayland behavior (VERIFICATION REQUIRED):** GTK window hints are best-effort; always-visible/focus-independent drag-drop for ordinary windows may be limited by Mutter. Nautilus "Send to AJ" and clipboard/file-chooser/CLI are supported fallback capture paths (host install not performed automatically).
- **Launch integration (IMPLEMENTED):** `aj orb` registered in top-level CLI and runtime checks; module form `python -m aj.orb` retained.


## 2026-11-11 Claude Web UI integration
- **Presentation vs backend (CURRENT DIRECTION):** embed the selected Claude React/Vite single-file UI in a WebKitGTK 4.1 + GTK3 host (`AJ/aj/orb_web.py`) instead of re-approximating visuals in Cairo. AJ Python owns canonical `InboxStore`, capture/process/retry, storage resolution, OS integration, and authoritative state; UI is presentation-only via JS bridge. Legacy GTK/Cairo orb retained as fallback.
- **Canonical inbox/storage (UNCHANGED):** no duplicate inbox/DB/queue/storage; same root precedence and no silent configured fallback; Home inbox preserved until approved verified migration.
- **Honesty over fake UX (CURRENT DIRECTION):** expose only backend-supported capabilities (retry, capture, open, quit); no fake byte progress/cancel/pause/chat.
- **GNOME Wayland strategy (VERIFICATION REQUIRED):** transparent overlay + dynamic input regions on XWayland/X11-capable session as implemented path; live acceptance required. If unsuitable, pivot to Nautilus/clipboard/chooser and/or approved GNOME Shell extension + IPC, not a generic GTK substitute that discards the selected UI.



## 2026-11-11 Step C crash/recovery evidence (continuation)
- **Evidence approach (CURRENT):** add deterministic real-subprocess tests (temp dirs, real JSONL/SQLite persistence, observable exit codes, OS signals/SIGKILL where feasible) to strengthen Step C without claiming exhaustive internal fault injection. Use production CLI/runtime entry points where practical; simulate state boundaries (torn appends, stale leases, uncommitted txns, killed holders) explicitly and report honestly.
- **Honesty gate:** P1-C/Step C strict matrix is not marked complete until required per-case passing evidence exists for all mandatory boundaries or remaining cases are precisely documented as non-provable with justification.


## 2026-11-11 Step C defensible checkpoint (gap closure)
- **Decision (evidence-based):** treat Step C as advanced to a defensible partial checkpoint (272/272, 20 real subprocess/boundary tests this session, explicit PASS/PARTIAL/NOT VERIFIED/NOT PRACTICALLY PROVABLE classifications). Do not mark P1-C complete. Do not add invasive production fault-injection hooks or unsafe controls solely for coverage claims; future closure of remaining micro-boundaries/durability limits requires an approved test-only seam design or dedicated crash-consistency/power-fault harness.


## 2026-11-11 Step D Hermes investigation (read-only)
- **Decision:** classify Hermes runtime as "gateway active/reachable now, LLM completions currently blocked by external provider credits/quota; AJ integration NOT ATTACHED" based on read-only evidence. No restart/reconfigure/kill/migration/attachment performed. Any AJ↔Hermes adapter/transport enablement requires explicit owner GREEN SIGNAL, approved permission/config scope, and verified stable interface — not assumed from service health.

## 2026-11-11 Step D interface decision (proposal, not yet approved)
- **Proposed boundary (requires owner approval):** AJ delegates to Hermes via the `api_server` platform's `/v1/runs` API (durable idempotency, SSE events, approval/stop endpoints, session continuity headers), behind a minimal `HermesExecutionAdapter` on the existing `ExecutionPort`. Rejected: gateway control socket (lifecycle-only), dashboard port (UI), `hermes --oneshot` (no run identity/idempotency/SSE/stop).
- **Not activated:** `platforms.api_server` remains disabled; no config edit, no gateway restart, no AJ flag flip. Activation waits on the HERMES GREEN SIGNAL and provider credits.


## 2026-11-11 Step E registry/dispatch decision
- **Decision:** registry metadata (`CapabilitySpec.executable`) and executor capability (`Aj.dispatch_of`) are separate, independently reported facts. A capability may not declare `available` unless some code path can actually run it; where that is not true the declaration is corrected rather than the dispatcher invented.
- **Applied:** `aj.delegate` and `helix.prepare_call` set to `unavailable` (no dispatcher: no AJ agent adapter; no `helix.calling_service` branch). This is a metadata correction inside the existing honesty rules, not an architecture change.
- **Consequence:** `aj capabilities` and `--check` now report `metadata_executable`, `dispatchable`, `dispatch_reason`; a regression test fails if any executable external capability lacks a dispatcher.
- **Not decided here:** whether to wire `helix.calling_service` (CallingService exists and is tested) or an AJ delegation resolver. Both change execution behaviour and need explicit approval — recorded as Step F item 2, not implemented.
