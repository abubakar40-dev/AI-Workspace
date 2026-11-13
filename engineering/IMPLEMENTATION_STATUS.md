# IMPLEMENTATION_STATUS.md
**Last updated:** 2026-11-11 (Step C gap closure advanced, 272/272; Hermes read-only investigation complete; Orb frozen)
**Workspace:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`

## Baselines (verified)
- **AJ:** `272 passed, 0 failed` (`cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q`, ~24.3s, 2026-11-11). `PYTHONPATH=. .venv/bin/python -m aj --check` exit 0, `ok: true`, Hermes **NOT ATTACHED**. AJ non-git; changes uncommitted/untracked (preserved).
- **JARVIS:** `514 passed, 2 failed` (`tests/test_voice_fixes.py::test_boot_speaks_the_greeting_not_the_briefing`, `test_the_audio_writer_uses_the_lock`) — known, deferred to Phase 6, untouched.
- **HELIX:** no conventional `test_*.py` suite; runtime/bridge/UI **VERIFICATION REQUIRED**.
- **Hermes:** `hermes-gateway.service` active (gateway, WhatsApp bridge, supervisor, proxy, socket/listener observed); read-only inspection only.

## Step A — Reconcile checkpoint: DONE (VERIFIED)
- Live state reconciled; backup `backups/campaign_checkpoint_20261111T042718Z/` preserved.

## Step B — Phase 2 Inbox/Orb: SUBSTANTIALLY COMPLETE (core VERIFIED)
- Inbox: SQLite WAL, originals/extracted/metadata/index separated, states/retry/archive/annotations/dupes, file/url/text capture+URL routing, graceful optional deps, CLI/viewer/worker, resilience tests, E2E proof (URL+file→ready), subprocess capture→restart-visibility.
- Orb/helpers: GTK3 orb (system Python), import-safe, smoke-started; autostart helper; `scripts/install_nautilus_send_to_aj.sh`, `integrations/aj-inbox-worker.service` added (not host-installed/long-run verified).
- **VERIFICATION REQUIRED:** interactive orb on live GNOME Wayland, Nautilus host install, worker long-run, richer optional extractor/network cases.

## Step C — Phase 1 strict crash-matrix: PARTIAL (defensible checkpoint, 2026-11-11)
- **OPERATIONALLY GREEN:** AJ **272/272 passed, 0 failed**; `aj --check` exit 0, `ok: true`, Hermes **NOT ATTACHED**.
- **New deterministic evidence (VERIFIED):** 20 real subprocess/signal/persistence/boundary-construction tests total this session: `AJ/tests/test_step_c_subprocess_crash_matrix.py` (12) and `AJ/tests/test_step_c_gap_closure.py` (8). Covers startup/shutdown/restart, backend exception propagation, corrupt/torn state + honest reporting, interrupted appends without loss of prior committed records, stale lease recovery incl. SIGKILL, conflicting operation serialization, repeated crash/restart cycles, SQLite memory reopen/WAL integrity + uncommitted-txn rollback, flock release on kill, constructed boundaries for lease-acquired-before-exec (4), attempt-started/lease-held interruption (7), receipt+journal-evidence-before-completion inconsistency (8/9 approximation), persisted retry-transition interruption (10 approximation), SIGKILL during recovery + repeated recovery convergence (14), and reconciliations A/D/E. See `engineering/audits/2026-11-11-step-c-crash-recovery-evidence.md` and `engineering/audits/2026-11-10-phase1-crash-matrix-mapping.md`.
- **Defensible checkpoint decision:** meaningful reliability value added; further closure of precise internal micro-boundaries (1,3,5,6,8,9,10,11,12 timing windows) and exhaustive B/C/F proofs requires test-only fault-injection seams or a crash-consistency/power-fault harness. Ordinary subprocess tests cannot prove power-loss/fsync/hardware-durability boundaries. **P1-C remains PARTIAL / VERIFICATION REQUIRED** (not complete). Step D proceeds in parallel with this honest classification.

## Step D — Hermes inspection: PARTIAL (read-only, evidence-based, 2026-11-11)
- **Current runtime (VERIFIED read-only):** Hermes v0.23.0 (git, `~/.hermes/hermes-agent`), `hermes-gateway.service` active/running; gateway PID 548124 (`Ssl`) with whatsapp bridge 548360 and supervisor 548361, listener `127.0.0.1:33143`, unix sockets `gateway.sock`/loop-tick; `gateway_state.json` running/whatsapp connected/session_store ok. Recent logs show provider **402 credit/quota exhaustion** for `openrouter/auto` and exhausted fallbacks (gateway alive but successful LLM completions currently blocked by provider/billing). Separate `/tmp/omnirush-hermes` proxy process observed.
- **STAT T discrepancy:** previously reported stopped/traced Hermes Python process **NOT OBSERVED now** (all current Hermes processes running/sleeping); cause not retroactively determinable. Health cannot be inferred from systemd active alone.
- **Interfaces/stores/skills (observed):** CLI (`hermes`, `hermes gateway`), loopback TCP+unix sockets, rich home/install skills+plugins, `state.db`/`projects.db`/`kanban.db`/`cron/executions.db`, sessions/logs/whatsapp state. Live end-to-end request completion, skill execution, structured task return, and failure-recovery behavior **NOT VERIFIED** in this pass (no safe synthetic execution; provider credits blocking completions).
- **AJ integration (VERIFIED):** boundary reserved but **NOT operational** — `UnavailableExecutionAdapter` only, no Hermes adapter/transport/socket task client in AJ, `hermes.execute_skill` unavailable/planned, config/flags gate, `aj --check` reports `hermes: NOT ATTACHED`. No automatic attachment/config change performed.
- **Audit:** `engineering/audits/2026-11-11-hermes-runtime-investigation.md`.

## Step E — Feature inventory: COMPLETE (2026-11-11, evidence-based)
- `engineering/audits/2026-11-11-step-e-inventory.md`: full AJ module/lifecycle/CLI inventory, capability registry audit, JARVIS/HELIX/Hermes inventories, capability dependency map, dependency/resource audit, 35-row unified maturity matrix, verified integration status, gaps, ordered Step F backlog.
- **Capability numbers verified from a real `build()`:** 40 registered = 26 JARVIS catalogue + 12 declared + 2 internal. Metadata-executable **was 4 → corrected to 2**; executor-dispatchable **3** (`aj.echo`, `aj.health_check`, `hermes.execute_skill` via port); runtime-verified execution **2**.
- **Why only two run:** `Aj._execute` has exactly three branches — `internal:*`, HERMES execution port, agent adapter by owner. There is no resolver for `helix.calling_service`, `device_bridge:*`, `jarvis.tool`, or `aj.orchestrator`, so `CallingService` (387 LOC, tested) is never invoked and `aj.delegate` had no AJ adapter at all.
- **Registry honesty fix (IMPLEMENTED, VERIFIED):** added `Aj.dispatch_of()` + `metadata_executable`/`dispatchable`/`dispatch_reason` reporting (`aj/orchestrator.py`, `aj/runtime.py` `--check`, `aj capabilities`); corrected the two false declarations (`aj.delegate`, `helix.prepare_call`) to `unavailable` with dated notes. Guarded by `AJ/tests/test_step_e_registry_dispatch.py` (9 tests), including a regression check that no metadata-executable external capability lacks a dispatcher.
- **Evidence:** `pytest -q` → **281 passed in 23.92s**; `aj --check` → exit 0, `ok: true`, `failures: []`, `dispatchable_ids = [aj.echo, aj.health_check, hermes.execute_skill]`.
- **Runtime facts recorded:** AJ has no systemd unit, no autostart entry and is not on PATH (library + CLI only); JARVIS (8875) and HELIX (8765) both down; port 8765 is held by an unrelated `mamba_desktop` process, so AJ's TCP probe reports a false HELIX "reachable".
- **Not done (needs approval):** wiring the first external dispatcher (`helix.calling_service`) — behaviour/architecture change, left as proposal.

## Step F — AJ core / campaign: IN PROGRESS
- **F1 Capability registry (IMPLEMENTED, VERIFIED):** `AJ/aj/capability.py` hardened/backward-compat extended — `CapabilitySpec` now supports `version`, `input_schema`, `output_schema`, `health`, `failure_modes` (serialized in `to_dict`/`from_dict`, defaults preserved). Existing declarations/behavior/tests compatible; AJ suite/check green.
- **F5 Canonical memory boundary (IMPLEMENTED, VERIFIED):** `AJ/aj/memory.py` adds `MemoryPort` protocol (raw events + derived summaries/search/stats/verify, provider-independent boundary) with `MemoryStore` as default local implementation.
- **F2/F3/F4:** existing permissions/task lifecycle/audit foundations inspected; further integration hardening continues (preserve behavior, no parallel security/lifecycle models).
- **F6–F10 onward:** provider gateway hardening, JARVIS/HELIX/Hermes integration, adapters, UI/voice/security/reliability/final integration — pending.

## Artifacts (this continuation segment)
- Added: `AJ/tests/test_inbox_subprocess_recovery.py`, `AJ/integrations/aj-inbox-worker.service`, `AJ/scripts/install_nautilus_send_to_aj.sh`, `engineering/audits/2026-11-10-phase1-crash-matrix-mapping.md`, `engineering/audits/2026-11-10-hermes-inventory.md`, `engineering/FEATURE_INVENTORY.md`.
- Modified: `AJ/aj/memory.py` (MemoryPort), `AJ/aj/capability.py` (registry spec hardening), `engineering/IMPLEMENTATION_STATUS.md`, `engineering/KNOWN_ISSUES.md`, `engineering/DECISIONS.md`.

## Next actions
0. **F2 (next):** capability dispatch architecture — add the first real non-internal resolver (`helix.calling_service` via existing `CallingService`), gated by `dispatch_of`, then re-run suite + `--check`; and identity-verified agent probes (TCP success ≠ HELIX).
1. **C:** implement highest-value deterministic subprocess kill/restart tests for AJ task boundaries (priority 4,5,7,8,9 where feasible), run full AJ suite, update matrix/A–F with evidence or precise non-provability.
2. **D/E:** deepen Hermes protocol/skill/integration/runtime evidence and expand JARVIS/HELIX concrete feature/runtime inventory (safe smokes).
3. **F:** continue registry/permission/task-lifecycle/audit integration hardening, provider gateway and memory/provider boundaries, then JARVIS/HELIX/Hermes integration and remaining master phases (JARVIS voice Phase 6 only), verifying/documenting continuously.


## 2026-11-11 continuation (F2 permission enforcement hardening)

- **AJ baseline (VERIFIED):** `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **217 passed, 0 failed** (~7.5s). `PYTHONPATH=. .venv/bin/python -m aj --check` → **exit 0** (all checks OK). Hermes remains **NOT ATTACHED**.
- **F2 Permission enforcement (IMPLEMENTED, PARTIALLY VERIFIED):**
  - Hardened `AJ/aj/orchestrator.py`: `retry` and `recover` now re-run capability blocker checks and `Authorizer.authorize(...)` at re-execution boundary before transitioning into execution/replay; consequential actions cannot be retried/recovered without fresh valid approval bound to payload (no stale/invalid authorization bypass). Refusals emit structured audit evidence (`retry_refused`/`recovery_refused`) and do not execute side effects.
  - `resume` (scheduler path) now enforces capability blocker/spec presence before execution (partial hardening; already-authorized consequential resume semantics remain **VERIFICATION REQUIRED**).
  - Fixed `inspect()` bugs: `journal.events(...)` instead of nonexistent `query(...)`, and safe lease state derivation (no `is_active()` assumption).
  - Added `AJ/tests/test_f2_permission_enforcement.py` (**11 tests, all passing**) covering: unauthorized side-effecting handle blocked, permitted read-only executes, valid approval allows intended op, approval cannot authorize different op/payload, invalid approval rejected, retry/recovery cannot bypass permission denial for consequential capability (real paths, no execution), retry with fresh valid approval succeeds, unknown capability fails safely, permission decisions produce audit evidence, forbidden capability never executes.
  - Execution-path matrix: `engineering/audits/2026-11-11-f2-execution-path-matrix.md`.
- **F3 Task lifecycle (EXISTING, PARTIALLY VERIFIED):** transition table/terminal states, leases, retry limits, recovery classification, dependency blocking/cycle detection, idempotency store, receipts/journal, and 14 multiprocess crash-safety tests remain in place (suite green). Formal per-boundary matrices and additional deterministic subprocess proofs for points 4,5,7,8,9/1,10,14 — **VERIFICATION REQUIRED / IN PROGRESS**.
- **F4 Durable audit/event integration (EXISTING, PARTIALLY VERIFIED):** append-only JSONL audit with redaction/locking, journal, receipts, task/memory event recording in key paths (including new retry/recovery refusal audits). Event coverage/correlation/mandatory-failure policy gaps and explicit classification (diagnostic vs required security audit vs transactional state) — **VERIFICATION REQUIRED**.
- **F5 Canonical memory (MemoryPort + MemoryStore, EXISTING/VERIFIED baseline):** `aj --check` memory/summary checks pass; raw/derived separation, verify, rebuildable summaries, backup/restore transfer checks present. Additional guarantee tests (derived-index failure isolation, rebuild proofs, provenance completeness, fresh-process recovery/restore cases per directive) — **VERIFICATION REQUIRED**.
- **Step C / D / E:** unchanged in substance from prior checkpoint; Step C strict 1–16/A–F external kill coverage still **VERIFICATION REQUIRED** (bounded, not blocking). Hermes/JARVIS/HELIX integration/runtime evidence remains **PARTIAL / VERIFICATION REQUIRED** (Hermes active, AJ attachment NOT ATTACHED).
- **Backups:** prior checkpoint backup preserved; incremental pre-change backup `backups/f2_f4_incremental_20261111/` contains `orchestrator.py`, `permissions.py`, `audit.py`, `task.py`, `memory.py`, `runtime.py`, `calling.py`.


## 2026-11-11 continuation b (scheduler resume + evidence docs)

- **F2 scheduler/resume (IMPLEMENTED, PARTIALLY VERIFIED):** `AJ/aj/orchestrator.py` resume now re-authorizes PLANNED/BLOCKED promotions (consequential tasks require approval, no auto-execute) and enforces blockers/capability consistency on AUTHORIZED continuation; `AJ/aj/scheduler.py` resumes leased task safely (`leased=True`). Added `AJ/tests/test_f2_scheduler_resume.py` (6 tests) — **all passing**. Stale-policy revalidation for pre-authorized AUTHORIZED consequential continuations remains **VERIFICATION REQUIRED** (consumed single-use approval model).
- **Evidence docs added:** `engineering/audits/2026-11-11-task-transition-matrix.md`, `engineering/audits/2026-11-11-task-ownership-and-recovery.md`, `engineering/audits/2026-11-11-audit-coverage-matrix.md`, `engineering/audits/2026-11-11-memory-guarantees.md`; updated F2 matrix and bounded Step C note in `engineering/audits/2026-11-10-phase1-crash-matrix-mapping.md`.
- **Verification:** `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_f2_scheduler_resume.py tests/test_f2_permission_enforcement.py` → **17 passed**. Full suite `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **217 passed, 0 failed**. `PYTHONPATH=. .venv/bin/python -m aj --check` → **exit 0**.
- **F3/F4/F5:** matrices and guarantees documented from code/runtime evidence with explicit gaps; no new transactional outbox or parallel systems; mandatory-audit-failure blocking and exhaustive memory/cancellation/idempotency proofs remain **VERIFICATION REQUIRED**.

## 2026-11-11 continuation c (durable auth context + stale-policy, bounded evidence)

- **F2 stale-policy closure (IMPLEMENTED, PARTIALLY VERIFIED):** added durable `TaskRecord.authorization_context` and `Aj` stale-authorization revalidation on AUTHORIZED resume continuations (version/risk/approval-stricter/forbidden/unavailable/payload-fingerprint/capability changes, missing/malformed context). Consequential stale/legacy continuations fail closed to `RECOVERY_REQUIRED` with audit/journal/memory evidence and no side effect; fresh authorized handle requests can proceed with valid current approval. Non-consequential legacy tasks without context may continue only when safely executable and not stricter (documented).
- **Tests:** `AJ/tests/test_f2_authorization_context.py` → **12 passed**. Combined with prior F2 tests: `tests/test_f2_scheduler_resume.py tests/test_f2_permission_enforcement.py tests/test_f2_authorization_context.py` → **29 passed**.
- **Regression fix:** made `TaskRecord` auth-context serialization/import robust for non-dict/redacted legacy values (resolved transfer/health regressions introduced during implementation).
- **Verification:** `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **229 passed, 0 failed**. `PYTHONPATH=. .venv/bin/python -m aj --check` → **exit 0** (all OK, Hermes NOT ATTACHED).
- **F4/F5/F3/Step C/D-E:** no new enforcement/proof implementation beyond existing evidence docs this segment; audit-failure policy enforcement, exhaustive memory proof tests, lifecycle/lease/cancellation/idempotency hardening, deterministic crash interruption proofs, and runtime cross-project integration evidence remain **IMPLEMENTATION/VERIFICATION REQUIRED** (see phase report).



## 2026-11-11 continuation d (F4 audit enforcement + F5 memory proofs)

- **Backup (VERIFIED):** `backups/f4f5_continuation_20261111T064709Z/` contains `AJ/aj` and `AJ/tests` (created before risky changes).
- **AJ baseline (VERIFIED):** pre-change `229 passed, 0 failed`; post-change `240 passed, 0 failed` (`cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q`). `aj --check` **exit 0**, `failures: []`, `attached: {"jarvis": false, "helix": false, "hermes": "NOT ATTACHED"}`.
- **F4 scoped audit enforcement (PARTIALLY IMPLEMENTED/VERIFIED):** `aj/audit.py` adds policy-aware `AuditLog.record(..., mandatory=False)` and non-swallowing `JsonlAuditSink.write` raising so mandatory failures propagate; `Aj.handle` now treats `awaiting_approval`, `policy_denied`, and pre-execution `authorized` as mandatory security audit points and fails safely without protected side effects on persistence failure. `tests/test_f4_audit_enforcement.py` (**4 passed**) proves controlled mandatory sink-failure blocking (no side-effect execution, no false persisted event, accurate structured failure) and best-effort diagnostic non-blocking. Not all emitters/paths (retry/recover/resume/adapter/calling) are uniformly enforced; no outbox/atomic cross-store guarantees — **PARTIAL**.
- **F5 canonical memory proofs (IMPLEMENTED/VERIFIED, isolated temp stores only):** `tests/test_f5_memory_proofs.py` (**7 passed**) proves raw preservation under summary failure, search-failure isolation without raw mutation, derived isolation/rebuild/delete-derived/rebuild equivalence without raw duplication/mutation, supported provenance/citation integrity, fresh subprocess reopen recovery, backup+verify with original temp store intact, and corruption detection (`verify` fails). No user stores touched. Full restore/import and all corruption/interruption classes remain **VERIFICATION REQUIRED**.
- **F2 bounded follow-up (PARTIAL):** `CallingService.confirm_and_dial` code-inspected as authorizer-gated before dial (runtime bridge evidence not rerun); `InternalActions.run` confirmed low-level unprotected API requiring orchestrator boundary; Hermes adapter/runtime **BLOCKED (NOT ATTACHED)**; same-task re-approval workflow **NOT IMPLEMENTED** (stale consequential continuations remain fail-closed `RECOVERY_REQUIRED`).
- **F3/Step C:** no new deterministic lifecycle/crash-boundary tests added this segment; existing suite remains green. **VERIFICATION REQUIRED** for remaining boundaries.
- **Preserved baselines:** JARVIS **514 passed, 2 known failures** untouched; HELIX prior bridge self-test status preserved; Hermes active/read-only **NOT ATTACHED**.


## 2026-11-11 AJ Orb campaign (desktop capture subsystem)
- **Continuation fixes (verified):** Cairo render crash fixed (smoke GUI starts without draw tracebacks), `AJ_INBOX_ROOT` strict-config regression fixed, `send_to_aj.py` now truthful for missing/non-file inputs with JSON results and multi-file/env-root capture verified; Nautilus installer supports dry-run/uninstall/batching. Full suite remains **247 passed**, `aj --check` exit 0.

- **Scope:** Orb subsystem + minimum supporting AJ interfaces only. No restart/rebuild of completed AJ core/F2-F5 work; Hermes remains **NOT ATTACHED**. Pre-change backup `backups/orb_campaign_20261111T082401Z/` verified.
- **Implemented (code):** rewrote `AJ/aj/orb.py` (GTK3/Cairo lightweight orb, state visuals, async capture worker/events, drag-drop multi-URI/file/URL/text with folder/unsupported feedback, clipboard paste, file chooser capture, process/retry/pause/open viewer/folder/summary/recent actions, position/state persistence with clamping, per-inbox single-instance lock, writability preflight, canonical config-aware inbox resolution). Added top-level `aj orb` CLI with `--inbox-root/--debug/--check-gui/--system-python/--json` and system-Python GTK fallback (no venv mutation). Hardened canonical inbox resolution in `aj/inbox.py`/`aj/inbox_cli.py` (explicit > `AJ_INBOX_ROOT` > config `core.inbox_root` > `core.data_dir/knowledge-inbox` > legacy home; no silent configured fallback). Updated runtime CLI checks and helper scripts (`orb_autostart.py`, `scripts/send_to_aj.py`, `scripts/install_nautilus_send_to_aj.sh`).
- **Tests/checks (VERIFIED):** `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **247 passed, 0 failed** (includes existing 10 inbox resilience/recovery + 7 new `tests/test_orb_non_gui.py`). `PYTHONPATH=. .venv/bin/python -m aj --check` → **exit 0, ok true**, Hermes **NOT ATTACHED**. System GTK runtime: `cd AJ && PYTHONPATH=. /usr/bin/python3 -m aj.orb --check-gui` → ok. Venv reports GTK unavailable clearly (expected; no gi in venv).
- **Docs:** `AJ/docs/10_AJ_ORB.md`, `engineering/audits/2026-11-11-aj-orb-campaign.md`.
- **Storage:** existing Home inbox `~/.local/share/aj/knowledge-inbox` preserved (not migrated). Effective default config still points to home `core.data_dir`; workspace-central path requires explicit `AJ_INBOX_ROOT`/`core.inbox_root`/`core.data_dir` and mount/writability. Migration requires safe stop/copy/verify/approval (not performed).
- **Status:** **PARTIALLY COMPLETE**. Live GNOME Wayland desktop behavior (no-disappear on focus, Nautilus drag-drop acceptance, notifications, monitor/workspace/scaling, long-run) is **VERIFICATION REQUIRED**; Nautilus/autostart/systemd host install **not performed**. Wayland always-on-top for ordinary GTK windows may be compositor-limited (documented).


## 2026-11-11 continuation (Claude Web UI integration into AJ Orb)

- **Backup:** `backups/orb_web_integration_20261111T175327Z/` preserved (`AJ/__main__.py`, `AJ/orb.py`, `AJ/runtime.py`, `10_AJ_ORB.md`, `IMPLEMENTATION_STATUS.md`, `KNOWN_ISSUES.md`, `DECISIONS.md`). `aj-orb-ui-generation/` left untouched.
- **Implemented (VERIFIED by build/import/checks):** vendored and integrated Claude UI in `AJ/orb_ui/` (bridge/real adapter/vector artwork/transparent-host hooks, `npm ci` + `npm run build` → `dist/index.html` 292.77 kB gzip 89.09 kB). Added `AJ/aj/orb_web.py` WebKitGTK 4.1 host embedding the bundle with JS bridge, canonical `InboxStore` snapshot/state mapping, async capture/process/retry worker, host DnD/chooser/clipboard/open/quit, region-based input shaping, position persistence, lock/writability preflight. Wired `AJ/aj/orb.py` and `AJ/aj/__main__.py` to prefer web host when available with GTK/Cairo fallback and preserved `--check-gui/--system-python/--inbox-root/--debug` semantics.
- **Automated verification (VERIFIED):** `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **252 passed, 0 failed**. Targeted: `tests/test_orb_non_gui.py` (7), `tests/test_orb_web_integration.py` (5), inbox suites green. `aj --check` → **exit 0, ok true**, Hermes **NOT ATTACHED**. System Python: `python -m aj.orb --check-gui` reports `ok/gtk/webkit/ui=web` and dist; mapping/snapshot smoke passed.
- **Status:** **IMPLEMENTED / AUTOMATED VERIFIED / LIVE DESKTOP VERIFICATION REQUIRED**. Interactive GNOME Wayland acceptance (visibility across focus/workspace/maximize/lock, real Nautilus drag-drop, notifications, screenshots, responsiveness), host installations (Nautilus/autostart/worker/extension), and Home→workspace inbox migration remain **NOT DONE / UNAPPROVED**. Active inbox remains `~/.local/share/aj/knowledge-inbox`.
- **Docs/audit:** updated `AJ/docs/10_AJ_ORB.md`, `engineering/IMPLEMENTATION_STATUS.md`, `engineering/KNOWN_ISSUES.md`, `engineering/DECISIONS.md`; added `engineering/audits/2026-11-11-aj-orb-web-ui-integration.md`.



## 2026-11-11 Step C continuation (crash/recovery subprocess evidence)

- **Orb:** untouched/frozen per directive (no UI/desktop/Wayland changes).
- **Implemented/verified:** added `AJ/tests/test_step_c_subprocess_crash_matrix.py` (12 real subprocess/signal/persistence tests, all passing). Evidence documented in `engineering/audits/2026-11-11-step-c-crash-recovery-evidence.md`.
- **Regression:** full suite `cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q` → **264 passed, 0 failed**. `aj --check` → **exit 0, ok true**, Hermes **NOT ATTACHED**.
- **P1-C status:** advanced with additional real evidence but **not complete**; exhaustive strict matrix/interruption proofs at all internal boundaries remain **VERIFICATION REQUIRED**.
- **Next:** continue Step C gap closure where deterministic/fault-injectable (or document precise non-provability), then Step D Hermes runtime/boundary investigation, Step E inventory, Step F core engineering toward real provider-independent conversational backend.


## 2026-11-11 Step C gap-closure continuation

- Added `AJ/tests/test_step_c_gap_closure.py` (8) covering constructed crash boundaries/reconciliations (points 4,7,8/9 approx,10 approx,14, A/D/E). Full suite **272 passed, 0 failed**; `aj --check` ok. No production code changes.
- **Decision:** Step C at defensible checkpoint with honest partial classification; P1-C not closed (internal micro-boundary fault injection and power-loss/fsync durability not practically provable without hooks/harness). Proceeding to Step D (read-only Hermes investigation).


## 2026-11-11 Step D continuation (Hermes read-only investigation)

- Completed read-only runtime/integration investigation (no restart/reconfigure/kill/migration/skill execution). Documented in `engineering/audits/2026-11-11-hermes-runtime-investigation.md`.
- **Readiness:** Hermes gateway currently running and reachable locally, but end-to-end LLM completions blocked by provider 402 credit/quota; AJ↔Hermes execution integration remains **NOT ATTACHED** (no adapter/transport). Small reversible integration work can be designed/implemented only with approved scope/GREEN SIGNAL; not performed automatically.
- **Next:** Step E — evidence-based feature/runtime inventory across AJ/JARVIS/HELIX/Hermes.

### Interface discovery (2026-11-11, read-only, decisive)
- `127.0.0.1:33143` = gateway-served **dashboard SPA**, not `/v1` (live probe: `/v1/health` and `/v1/skills` → `200 text/html`).
- `~/.hermes/gateway.sock` = **control socket** (lifecycle verbs only: identify/restart-pause/profile serve/reload/ticket) — no task submission.
- The real task API is the **`api_server` platform** (`POST /v1/runs`, `GET /v1/runs/{id}`, SSE `/events`, `POST .../{approval,steer,stop,resolve-unknown}`, `GET /v1/{capabilities,skills,toolsets}`; durable `runs_idempotency.db`; `max_concurrent_runs`→429; `API_SERVER_KEY` ≥16 chars). **It is NOT enabled** on this host (`platforms:` enables only `whatsapp`); enabling needs a config change + gateway restart = owner decision (HERMES GREEN SIGNAL).
- Therefore AJ↔Hermes remains **NOT ATTACHED** for engineering reasons now fully pinned down: no enabled task endpoint, not a missing adapter design.
