# Step E — Feature, Capability & Runtime Inventory (evidence-based)

**Date:** 2026-11-11  
**Scope:** AJ (full), JARVIS + HELIX (read-only), Hermes (read-only, continuing Step D). Orb frozen. No JARVIS/HELIX edits, no Hermes config/restart, no data migration.

**Rule applied throughout:** a class/function/CLI/config entry is not evidence of working behaviour. Every claim below is tagged with what was actually executed: source read, test run, or live probe.

---

## 0. Baseline re-verified before inventory

```
$ cd AJ && PYTHONPATH=. .venv/bin/python -m pytest -q
281 passed in 23.92s                      # 272 checkpoint + 9 new Step E tests
$ python -m aj --check
ok: true, failures: [], attached {jarvis:false, helix:false, hermes:"NOT ATTACHED"}
```

---

## 1. AJ core inventory

**Shape:** 36 modules in `aj/` (12,596 LOC incl. `aj/integrations/`), 26 test files (7,047 LOC), **zero runtime dependencies** (`pyproject.toml: dependencies = []`), requires Python ≥3.10, venv is 3.14.4.

| Module | LOC | Role | Persistence | Tests |
|---|---|---|---|---|
| `orchestrator.py` | 1740 | Control plane: `Router`, `Aj.handle/retry/cancel/recover/resume/inspect`, executor dispatch, audio of audit/journal/receipts | via stores | `test_orchestrator`, `test_phase2/3`, `test_f2_*`, `test_dead_letter` |
| `orb.py` / `orb_web.py` / `orb_autostart.py` | 1287 / 1134 / — | Orb capture UI + local web server (**frozen**) | inbox | `test_orb_non_gui`, `test_orb_web_integration` |
| `inbox.py` / `inbox_cli.py` / `inbox_view.py` | 698 / 372 / 186 | Knowledge-inbox capture pipeline (incoming→processing→processed/originals/thumbnails/metadata/index, failed) | directory tree + index | `test_knowledge_inbox`, `test_knowledge_inbox_resilience`, `test_inbox_subprocess_recovery` |
| `lease.py` | 563 | Worker leases, atomic lease JSON, history, expiry | `leases/*.json`, `lease-history.jsonl` | `test_crash_safety`, `test_step_c_*` |
| `runtime.py` | 538 | Assembly + `health()`/`--check` (23 checks) | — | `test_runtime` |
| `task.py` | 429 | Task state machine (18 states, `TERMINAL`), JSONL store w/ flock | `tasks.jsonl` | `test_foundation`, `test_phase2/3` |
| `calling.py` | 387 | `CallingService`, `CallRecord`, `DeviceBridge`/`NullDeviceBridge`, contact resolution | in-memory map | `test_calling` |
| `providers.py` | 361 | Provider adapters, credential-gated `usable()`, health TTL, fallback chain | health in memory | `test_providers` |
| `permissions.py` | 318 | 5-level ladder (read/low/user/consequential/sensitive), `allow|confirm|deny`, approval gate + TTL | — | `test_f2_*` |
| `contracts.py` | 314 | `AgentRequest/Result`, `ExecutionRequest/Result`, `SkillSpec` | — | contract tests |
| `capability.py` | 283 | `CapabilitySpec` + registry, honesty rules on availability/verification | `config/capabilities.json` | `test_foundation` |
| `audit.py` | 276 | Append-only JSONL audit + `_redact` + rotation | `audit/events-YYYY-MM.jsonl` | `test_f4_audit_enforcement`, `test_secrets_redaction` |
| `memory.py` | 272 | Canonical raw events + summaries (SQLite **WAL**) | `memory.sqlite3` | `test_memory`, `test_f5_memory_proofs` |
| `transfer.py` | 239 | export / import / backup / verify | files | `test_phase3` |
| `agents.py` | 234 | `HttpAgentAdapter` (TCP probe + no agreed transport ⇒ honest reject), `UnconfiguredAgent` | — | `test_orchestrator` |
| `execution.py` | 147 | `ExecutionPort`, `UnavailableExecutionAdapter`, `SkillRegistry`, `execute()` | — | `test_hermes_contract` |
| `journal.py` | 104 | Append-only execution journal | `journal.jsonl` | crash tests |
| `receipts.py` | — | Per-attempt receipt with verification status + journal ids | `receipts.jsonl` | crash/idempotency tests |
| `idempotency.py` | — | Key→task map w/ payload fingerprint | `idempotency.json` | `test_idempotent_replay` |
| `scheduler.py` | 98 | Resumable scheduling | — | `test_f2_scheduler_resume` **only** |
| `retention.py` | — | Retention policy | — | **no caller** |
| `invariants.py` | — | Transition invariants | — | imported by orchestrator, **unused** |

**Lifecycle / installation (verified live):**
- `aj` is **not on PATH**; no `aj*.service` in `systemctl --user`; no autostart entry. AJ is a library + `python -m aj` CLI, not a daemon.
- Data lives at `~/.local/share/aj` (212 KB): `tasks.jsonl`, `journal.jsonl`, `lease-history.jsonl`, `leases/`, `audit/`, `memory.sqlite3`, `knowledge-inbox/`.
- `receipts.jsonl` / `idempotency.json` are absent from the live dir **only because** `--check` runs its sub-checks against isolated paths; an isolated `aj.echo` run did produce `receipts.jsonl` with a full receipt (verified: task/operation/attempt/worker/lease ids, `execution_status`, `verification_status`, `journal_event_ids`, `schema_version: 1`).

**CLI:** 18 commands (`run, tasks, task, cancel, retry, audit, memory, summary, capabilities, permissions, config, diagnostics, export, import, backup, recover, orb, inbox`) — count verified from `_COMMANDS` and from `--check.checks.cli`.

---

## 2. Capability registry audit (the 40/2/18 question)

**Verified decomposition of "40":**

| Source | Count | Executable (metadata) | Dispatchable (executor) |
|---|---|---|---|
| `aj/actions.py` internal (`aj.echo`, `aj.health_check`) | 2 | 2 | 2 |
| `config/capabilities.json` (HELIX 10, AJ 1, HERMES 1) | 12 | was 2 → **now 0** | 1 (`hermes.execute_skill` via port) |
| `JARVIS/core/capabilities.py` imported catalogue | 26 | 0 | 0 |
| **Total** | **40** | **was 4 → now 2** | **3** |

**Why only two capabilities are executable — answered from code.** `Aj._execute` has exactly three dispatch branches:
1. `execution_adapter.startswith("internal:")` → in-process `InternalActions` (only `aj.echo`, `aj.health_check`);
2. `spec.owner_agent == "HERMES"` → `ExecutionPort` (currently `UnavailableExecutionAdapter`);
3. everything else → `AgentRegistry.find(owner)` → `HttpAgentAdapter`/`UnconfiguredAgent`.

There is **no resolver for `helix.calling_service`, `device_bridge:*`, `jarvis.tool`, or `aj.orchestrator`**. `CallingService` (387 LOC, tested) is never invoked by the orchestrator; `agents.py` has no AJ adapter at all. So the architecture is *intentional about the boundary* and *incomplete about the adapters* — not a bug, but a real gap between declared and executable capability.

**Defects found (and fixed — see §8):** two declarations claimed availability with no handler behind them:
- `aj.delegate` — `available` + `verified`, but `handle(capability_id="aj.delegate")` → `FAILED / agent_unavailable / "no adapter configured"`.
- `helix.prepare_call` — `available` + `partial`, but the adapter is ignored and routing goes to the HELIX HTTP adapter → `agent_unavailable`.

**Second, subtler defect (live evidence):** because `HttpAgentAdapter.available()` is a raw TCP connect, and `mamba_desktop` now listens on **8765**, AJ reported `HELIX.reachable = True` and produced the diagnostic *"HELIX is reachable but exposes no agreed AJ task endpoint"* — for a HELIX that is not running. `--check` still correctly reports `helix: false` (different code path), so the misleading string only surfaces in orchestration errors. Recorded as a known issue; not changed (would need an identity handshake that HELIX does not expose).

**Minimum work to make the registry genuinely useful:** (a) one dispatcher branch per adapter family, starting with `helix.calling_service` (already implemented and tested) and an AJ-side `aj.delegate`→default-route resolver; (b) keep the new `dispatchable` report as the gate so declared≠runnable cannot regress. Both are Step F items 2–3.

---

## 3. JARVIS inventory (read-only, no edits)

- **Architecture:** single large Python app (`main.py`, 3,400+ lines) + `core/` (`capabilities.py`, `policy.py`, `confirmation.py`, `audit.py`, `voice.py`), `agents/`, `actions/`, `tools/`, `desktop/`+`gui/`, `plugins/`, `dashboard/`.
- **Runtime entry:** `main.py:main()`; **UI/gateway bridge on `ws://127.0.0.1:8875`** (`bridge_ws.py: PORT = 8875`), spawned as `desktop_ui.py … ws://127.0.0.1:8875`.
- **Live state:** **not running** — nothing listens on 8875 (probe: connection refused). AJ reports `jarvis.reachable = False`.
- **Capabilities:** 26 declared in `core/capabilities.py`, all imported into AJ's registry with `availability: unknown` (28 unknown overall) → correctly non-executable by AJ policy.
- **LLM/providers:** `groq_client.py`, `or_client.py` (OpenRouter), `nrouter_client.py`, `ollama_client.py`, `claude_fallback.yaml`, `google-genai`; heavy local desktop automation (`pyautogui`, `mss`, `playwright`).
- **Memory:** `memory/`, `chat_history/`, `chat_history_manager.py`, `workspace_store.py`.
- **Dependencies:** `requirements.txt` = 34 entries, including **Windows-only** `comtypes`, `pycaw`, `win10toast`, `pywinauto`, `pygetwindow`; a separate `requirements-linux.txt` exists → dual-list drift risk.
- **Tests:** 18 files; known pre-existing `test_voice_fixes.py` failures preserved untouched (deferred to Phase 6).
- **AJ integration status:** adapter exists (`HttpAgentAdapter` → 8875), `protocol_verified: false`, **no agreed `/aj/task` endpoint**; bridge is WebSocket UI protocol, not an AJ task API. **Not operational.**

---

## 4. HELIX inventory (read-only, no edits)

- **Architecture:** small repo — `bridge/` (`bridge_ws.py`, `helix_desktop.py`, `.desktop` file), `tools/` (calls, whatsapp, live_server, lms_client, voice, browser, selfcheck), `agents/pc.md`, `docs/`.
- **Critical finding — HELIX is a Hermes front-end, not a general agent.** `bridge_ws.py` header: *"Reads real Hermes/Kanban state from `~/.hermes/kanban.db` and `~/.hermes/state.db`. Forwards UI commands to Hermes via `hermes kanban create` / CLI."* It speaks a UI WebSocket protocol on **8765** and serves the static UI over HTTP (`http_serve` is GET-only, path-traversal guarded). **There is no `/aj/task` task API.**
- **Live state:** **not running**. Port 8765 is currently owned by an unrelated `mamba_desktop --background` process (PID 140470) — the source of the false "HELIX reachable" signal in §2.
- **Dependencies:** stdlib only for the bridge (no external deps).
- **Tests:** no `tests/` directory; only in-file selftest (`_selftest`) and `tools/selfcheck.py`.
- **AJ integration status:** config points at `http://127.0.0.1:8765`; adapter exists; no protocol agreement; `helix.*` capabilities all non-executable after the metadata correction. **Not operational, and architecturally redundant with the Hermes boundary** (both would drive Hermes).

---

## 5. Hermes skill/runtime inventory (structural, nothing executed)

Baseline remains `engineering/audits/2026-11-11-hermes-runtime-investigation.md` (v0.23.0, gateway PID 548124 `Ssl`, dashboard on 33143, `api_server` **disabled**, `/v1/runs` = proposed boundary, provider 402).

**47 installed skills** under `~/.hermes/skills` (excluding `.hub`), across apple, autonomous-ai-agents, creative, devops, email, media, note-taking, productivity, research, social-media, software-development, web.

Keyword scan (heuristic, **not** a security verdict):

| Flag class | Skills | Corrected interpretation |
|---|---|---|
| credentials referenced | 18 | docs mention API keys/tokens; requires per-skill review before delegation |
| installs packages | 15 | `pip/npm/apt install` in instructions |
| external messaging | 6 | whatsapp/telegram/slack/discord/imessage |
| filesystem destructive | 4 | `claude-code`, `computer-use`, `microsoft-office`, `pdf` (rm -rf present in instructions) |
| outbound write/send | 4 | `git push` / POST calls |
| browser automation | 1 | playwright/computer-use |
| payment | **2 real** | `creative/claude-design`, `creative/popular-web-designs` (Stripe copy examples). The other 4 hits were **git `checkout`** false positives — corrected after inspection |
| no flags | 15 | simplest candidates for future delegation |

**Delegation suitability (proposal only):** read-only, bounded skills (e.g. `software-development/codebase-inspection`, `productivity/disk-usage-audit`, `research/arxiv`) are plausible first delegations. Anything with `rm -rf`, `git push`, messaging or credentials requires explicit per-skill authorization. **No skill was executed; no credits spent.**

---

## 6. Capability dependency map

```
CLI (__main__, 18 cmds) ──► runtime.assemble ──► orchestrator.Aj
                                                   │
        ┌──────────────────────────────────────────┼─────────────────────────────┐
        ▼                                          ▼                             ▼
  capability.Registry                      permissions.Authorizer         task.TaskStore (+invariants)
        │  (internal_specs ← actions.py;          │  (levels, approval TTL)        │
        │   config/capabilities.json;             │                               ▼
        │   JARVIS/core/capabilities.py)          │                        tasks.jsonl (flock)
        ▼                                          ▼
  executor dispatch                      audit.AuditLog ──► audit/*.jsonl
    ├─ internal:* ──► actions.InternalActions        │
    ├─ HERMES ─────► execution.ExecutionPort ────────┤ (UnavailableExecutionAdapter today)
    └─ else ───────► agents.AgentRegistry            │
                        ├─ JARVIS HttpAgentAdapter ──► ws://127.0.0.1:8875 (not running)
                        └─ HELIX  HttpAgentAdapter ──► :8765 (mbed/mamba, not HELIX)
        │
        ├─ journal.Journal ─────────► journal.jsonl
        ├─ receipts.ReceiptStore ───► receipts.jsonl
        ├─ lease.LeaseManager ──────► leases/*.json + lease-history.jsonl
        ├─ idempotency.Store ───────► idempotency.json
        └─ memory.MemoryStore ──────► memory.sqlite3 (WAL) ──► summary.py

Sibling independence: AJ imports JARVIS *capability metadata only* (integrations/jarvis_registry.py),
never JARVIS code paths. AJ never imports Hermes internals. HELIX bridges to Hermes on its own.
Unused/dormant: scheduler.py (tests only), retention.py (no caller), invariants.py (imported, unused),
calling.CallingService (tests only), orb_autostart (Orb frozen).
```

---

## 7. Dependency & resource audit (machine: i5-7300U, 8 GB RAM, Ubuntu 26.04.1, GNOME Wayland)

| System | Runtime | Deps | Notes |
|---|---|---|---|
| AJ | Python 3.14.4 (`.venv`) | **none** (`pytest` dev-only) | nothing to install, no daemon, ~212 KB state |
| JARVIS | Python 3.14.4 (`venv`) | 34 pins, incl. 5 Windows-only; `requirements-linux.txt` split | `playwright`/`pyautogui`/`mss` are heavy; dual lists can drift |
| HELIX | Python 3 (stdlib bridge) | bridge: stdlib only | subprocesses `hermes` CLI |
| Hermes | pinned Python **3.14.9** + Node 26.12.1, venvs under `installs/` | large plugin surface | gateway ~513 MB RSS (peak 2.4 GB), WhatsApp bridge + dashboard on 33143 |
| Third-party | — | `/tmp/omnirush-hermes/src/proxy.mjs` (Node, port 20129) | unrelated OpenAI-compatible proxy, not part of AJ |

Duplication/conflict notes: three separate Python 3.14 environments (AJ, JARVIS, Hermes toolchain) with no shared pin file; `fastapi/uvicorn` in JARVIS requirements but the live bridge is a hand-rolled websocket server; `duckduckgo-search` superseded upstream by `ddgs` (not changed without caller tracing). **Nothing was removed.**

---

## 8. Changes implemented during this inventory (small, reversible, tested)

**Problem:** registry metadata could advertise capabilities the executor cannot run, and `--check` offered no way to see the difference.

1. `aj/orchestrator.py` — added `Aj.dispatch_of(spec) -> (bool, reason)` (internal action / HERMES port / agent adapter with an agreed transport / otherwise false) and extended `capability_report()` with `metadata_executable`, `dispatchable`, `dispatch_reason`.
2. `aj/runtime.py` — `_check_orchestrator` now reports `metadata_executable`, `dispatchable`, `dispatchable_ids`.
3. `aj/__main__.py` — `aj capabilities` rows carry `dispatchable` + `dispatch_reason`.
4. `config/capabilities.json` — corrected the two false claims, with dated notes explaining the exact missing dispatcher:
   - `aj.delegate`: `available`→`unavailable`, `verified`→`implemented_unverified`.
   - `helix.prepare_call`: `available`→`unavailable` (CallingService exists and is tested; no dispatcher).
5. `AJ/tests/test_step_e_registry_dispatch.py` — **9 tests**, incl. a regression guard that no metadata-executable external capability lacks a dispatcher, and a subprocess CLI check.

**Evidence:**
```
$ pytest tests/test_step_e_registry_dispatch.py -q   → 9 passed in 0.49s
$ pytest -q                                          → 281 passed in 23.92s
$ python -m aj --check                               → exit 0, ok: true, failures: []
  orchestrator detail: capabilities 40, metadata_executable 2,
  dispatchable 3 (aj.echo, aj.health_check, hermes.execute_skill)
```

Net effect: `aj capabilities` no longer advertises `aj.delegate`/`helix.prepare_call` as runnable; selecting them now fails fast with `capability_unavailable` instead of a misleading downstream agent error. No execution semantics, permissions, or Hermes behaviour changed.

---

## 9. Unified feature maturity matrix

Statuses: **AV**=implemented+automated verified, **RV**=implemented+runtime verified, **NV**=implemented+not verified, **PI**=partially implemented, **RO**=registered/configured only, **DO**=dormant/disconnected, **BR**=broken, **PL**=planned.

| # | Feature | Owner | Implementation | Tests | Evidence | Status |
|---|---|---|---|---|---|---|
| 1 | Task state machine (18 states) | AJ | `task.py` | yes | `--check task_lifecycle` COMPLETED | AV |
| 2 | Task persistence (JSONL+flock) | AJ | `task.py`, `locking.py` | yes | `tasks.jsonl` live | AV |
| 3 | Leases + crash recovery | AJ | `lease.py`, `recovery.py` | yes | SIGKILL matrices | AV (micro-boundaries PARTIAL per Step C) |
| 4 | Journal / receipts | AJ | `journal.py`, `receipts.py` | yes | receipt observed in isolated run | AV |
| 5 | Audit + redaction | AJ | `audit.py` | yes | `--check audit` | AV |
| 6 | Canonical memory (SQLite WAL) | AJ | `memory.py` | yes | 28 KB live DB | AV |
| 7 | Summaries/verification | AJ | `summary.py` | yes | `--check summary` | AV |
| 8 | Idempotent replay | AJ | `idempotency.py` | yes | opt-in `idempotency_key` param | AV (opt-in) |
| 9 | Permission ladder + approvals | AJ | `permissions.py` | yes | `--check permissions` | AV |
| 10 | Capability registry | AJ | `capability.py` | yes | 40 entries | AV (honesty improved this pass) |
| 11 | Capability **execution** | AJ | `orchestrator._execute` | yes | 2 capabilities reachable | **PI** (3 dispatch branches only) |
| 12 | Provider gateway | AJ | `providers.py` | yes | `usable: 0` (no keys) | NV (no credential; no live call) |
| 13 | Internal actions | AJ | `actions.py` | yes | echo/health_check COMPLETED | RV |
| 14 | Calling foundation | AJ/HELIX | `calling.py` | yes | not dispatched | **DO** |
| 15 | Scheduler | AJ | `scheduler.py` | test-only | no runtime caller | **DO** |
| 16 | Retention | AJ | `retention.py` | none | no caller | **DO** |
| 17 | Knowledge inbox | AJ | `inbox*.py` | yes | live tree + subprocess recovery | AV |
| 18 | Export/import/backup | AJ | `transfer.py` | yes | `--check transfer` | AV |
| 19 | Diagnostics | AJ | `diagnostics.py` | yes | `--check diagnostics` | AV |
| 20 | CLI (18 commands) | AJ | `__main__.py` | yes | `--check cli` | AV |
| 21 | Orb capture UI | AJ | `orb.py`, `orb_web.py` | yes | **frozen by directive** | AV (frozen) |
| 22 | JARVIS delegation | AJ→JARVIS | `agents.py` | yes | 8875 refused | **DO** |
| 23 | HELIX delegation | AJ→HELIX | `agents.py` | yes | 8765 is not HELIX | **DO** (false-positive probe) |
| 24 | Hermes execution | AJ→HERMES | `execution.py` | contract only | `NOT ATTACHED` | **PL/RO** |
| 25 | JARVIS app runtime | JARVIS | `main.py`, `bridge_ws.py` | 18 files | not running | NV (source exists) |
| 26 | JARVIS 26 tools | JARVIS | `core/capabilities.py` | — | imported as metadata | RO |
| 27 | JARVIS voice | JARVIS | `core/voice.py` | `test_voice_fixes` | known failures | **BR** (preserved, Phase 6) |
| 28 | HELIX UI bridge | HELIX | `bridge_ws.py` | selftest | not running | DO |
| 29 | HELIX→Hermes forwarding | HELIX | subprocess `hermes kanban create` | none | code present | NV |
| 30 | Hermes gateway | Hermes | service | n/a | PID 548124 `Ssl`, active | RV (process-level) |
| 31 | Hermes LLM completion | Hermes | provider | n/a | HTTP 402 | **BR** (external credits) |
| 32 | Hermes `/v1/runs` task API | Hermes | `api_server` | upstream | platform disabled | **RO/DO** (config-gated) |
| 33 | Hermes skills (47) | Hermes | `~/.hermes/skills` | n/a | structural scan | NV (none executed) |
| 34 | Hermes approval gating | Hermes | `/v1/runs/{id}/approval` | upstream | not mounted | RO |
| 35 | Conversational backend | — | — | — | no LLM turn path in AJ | **PL** |

**Honest totals:** executable-by-metadata **2**, dispatchable **3**, runtime-verified execution **2** (plus 1 dispatch-only). No percentage completion is claimed.

---

## 10. Verified integration status

| Link | Config | Adapter | Runtime | E2E |
|---|---|---|---|---|
| AJ → JARVIS | yes (8875) | yes | **no** (refused) | **no** |
| AJ → HELIX | yes (8765) | yes | port open by **foreign process** | **no** |
| AJ → Hermes | gated off | `UnavailableExecutionAdapter` | **no** | **no** |
| HELIX → Hermes | hard-coded path | subprocess | HELIX not running | **no** |
| Hermes gateway → providers | yes | yes | gateway up | **no** (402) |
| AJ → Orb | yes | yes | tests pass | local only (frozen) |

---

## 11. Critical architectural gaps

1. **No conversational backend anywhere in AJ.** `Router.route` sends text to JARVIS by default; there is no LLM turn, no prompt assembly, no response synthesis. This is the true blocker behind the Orb freeze.
2. **Registry ↔ executor gap.** 37 of 40 capabilities have no dispatch handler; the new `dispatchable` report makes this visible instead of implied.
3. **No agreed task protocol with any sibling.** Both HTTP adapters lack a transport; `protocol_verified` is `false` everywhere.
4. **Port-based readiness is not identity-based.** A foreign listener satisfied the HELIX probe.
5. **Three Python 3.14 environments** and a JARVIS dependency list that cannot install on Linux as written.
6. **Dormant-but-tested modules** (scheduler, retention, calling, invariants) create a false sense of completeness in test counts.
7. **Hermes blocked externally** (402) and by design (`api_server` disabled).

---

## 12. Ordered Step F backlog

| # | Item | Missing | Reuse | Risk | Acceptance |
|---|---|---|---|---|---|
| 1 | Core runtime reliability | Step C micro-boundaries (env-limited) | 280 tests, leases, journal | low | no regression; classify, don't fake |
| 2 | Capability dispatch architecture | resolvers for `helix.calling_service`, `aj.delegate`, `internal:` registration path | `CallingService`, new `dispatch_of` | medium | ≥1 new adapter family dispatchable with tests; `dispatchable` rises without metadata lies |
| 3 | Permission/trust boundary for delegation | per-capability approval proof at dispatch | `permissions.py`, `Authorizer` | medium | consequential capabilities cannot run without `confirm`+token; tests |
| 4 | Unified task/execution contract | one contract shared by internal/agent/runtime | `contracts.py` | medium | single `ExecutionResult` normalization across 3 branches |
| 5 | Canonical memory ↔ conversation | no conversation events in memory | `memory.py` events | low | chat turns persisted as raw events (when a chat path exists) |
| 6 | Provider-independent LLM gateway | live adapter proof | `providers.py` | low (needs key) | one real completion through `ProviderGateway` with fallback |
| 7 | Real conversational backend | routing, prompts, streaming, history | inbox/memory/audit | **high** | text in → LLM answer out, audited, provider-agnostic |
| 8 | Hermes task adapter | `/v1/runs` client + enablement approval | `execution.py` port | high (owner gate) | idempotent submit, SSE, stop, approval surfaced |
| 9 | JARVIS/HELIX contracts | agreed `/aj/task` protocol, identity handshake | `HttpAgentAdapter` | medium | probe verifies identity, not just TCP |
| 10 | Orb resumption | depends on #7 | frozen Orb code | high | only after real LLM responses exist |

---

## 13. Highest-priority next task (begun this pass)

Per the approved ordering (core reliability → capability architecture → trust boundary), item **2** is the first actionable one that is not environment-blocked, and the inventory exposed a concrete, verified defect inside it: **metadata executability was disconnected from the dispatch table.** That is now fixed and guarded by tests (§8). The next increment in the same thread — wiring the first real external adapter family (`helix.calling_service`, already implemented and unit-tested) — is a behavioural/architecture decision that needs approval, so it is left as a proposal rather than silently implemented.

## 14. Commands actually executed (representative)

```
pytest -q; pytest tests/test_step_e_registry_dispatch.py -q; python -m aj --check
python - <<'PY' (build/registry dumps, dispatch probes, isolated aj.echo run)
aj capabilities --json   (subprocess, isolated data dir — via test)
ss -ltnp | grep -E "8875|8765|33143|3000"
curl -m 3 http://127.0.0.1:{8875,8765}/health          → refused / reset
ps -o pid,ppid,stat,etime,cmd -p 548124,140470
systemctl --user list-units --all | grep -i aj          → none
find ~/.hermes/skills -name SKILL.md | wc -l            → 47
grep/wc over aj/, tests/, JARVIS/, helix/ for the module, state and dependency tables above
```
