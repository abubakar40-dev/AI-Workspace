# Feature → Code Traceability

Every capability from the approved catalogue, mapped to the code that actually implements
it, with an honest status. "Present" means the code exists and is reachable; it does **not**
mean it was verified at runtime. Verification status is in its own column.

Status vocabulary: **complete** (implemented + exercised) · **partial** · **broken** ·
**present-unverified** (reachable, not exercised here) · **dead** (exists, unreachable) ·
**missing** · **deferred**.

---

## 3.1 Identity and orchestration

| Feature | Project | Status | Files / symbols | Execution path | Evidence |
|---|---|---|---|---|---|
| Distinct identities | JARVIS, HELIX | complete | `core/prompt.txt` (16 lines); `core/voice.py::IDENTITY_PROMPT`; helix `HELIX_RIDER` | model system instruction | Source |
| Direct addressing | both | present-unverified | wake phrases in `core/voice.py` | model-side | Not audible-tested |
| Central orchestration | JARVIS | partial | `agent/planner.py`, `orchestrator.py`, `supervisor.py`, `helix_manager.py` | `agent_runtime.start()` | `main.py` subscribes to events |
| Agent routing | JARVIS | partial | `agent/executor.py::_call_tool`, `agents/*.md` | planner → executor | 357 test functions, no orchestration test |
| Multi-step tasks | JARVIS | partial | `agent/runtime.py` queue + worker | background thread | No durable checkpointing |
| Task state / lifecycle | JARVIS | **missing** | — | — | No receipt, no resume, no dedupe |
| Error recovery / retry | JARVIS, HELIX | partial | `agent/error_handler.py`, `error_logger.py`; helix `selfcheck.py` | inline try/except | No policy object, ad-hoc |
| Task deduplication | JARVIS | missing | — | — | — |
| Execution receipts / history | JARVIS | partial | `workspace_store.py`, `chat_history_manager.py` | task workspace UI | UI-level, not durable |
| Delegate to specialists | JARVIS | complete | `agent_task` → `agent/` | dispatch → runtime | Live, tested indirectly |
| Human oversight | JARVIS | **partial** | `core/policy.py`, `core/confirmation.py` | `executor._call_tool` | **Gated on agent path only**; live chain ungated |

## 3.2 Voice — one shared core

| Feature | Project | Status | Files | Notes |
|---|---|---|---|---|
| Voice contract (single source) | **shared** | complete | `JARVIS/core/voice.py` (4,881 B) | model, voice, wake phrases, persona, rates, key |
| HELIX consumes the core | HELIX | complete (structural) | `helix/tools/live_server.py`, `live_tts.py`, `helix_voice.py` | import `core.voice`; hard-fails if absent |
| Second HELIX core | HELIX | **removed** | — | three independent configs collapsed to one import |
| Mic capture | JARVIS | present-unverified | `JarvisLive` | 16 kHz PCM16 |
| Speech detection (VAD) | both | **missing** | — | candidate: Silero VAD (MIT) |
| STT | JARVIS | present-unverified | Gemini input transcription | model-side, not local |
| TTS | JARVIS | present-unverified | `actions/attention_monitor` hooks + Edge TTS; `bridge_ws._render` chain | 4 tiers: live-tts → edge → piper → espeak |
| Audio output | JARVIS | present-unverified | `audio_in_queue` → 24 kHz | — |
| Interruption | JARVIS | present-unverified | mic stays open; `interrupted` handled | **Not audible-tested** |
| Wake word | JARVIS, HELIX | partial | prompt-level only | no detector; candidate openWakeWord |
| Push-to-talk | — | missing | — | — |
| Lifecycle / restart | both | partial | service units | `helix-live` supervised; JARVIS manual |

Known voice defects: `_send_realtime` writes without the session lock; boot greeting no
longer spoken. Both are covered by the two failing tests. See `JARVIS_COMPLETE_AUDIT.md` §3.

## 3.3 Memory and knowledge

| Feature | Status | Files | Notes |
|---|---|---|---|
| Persistent memory | complete | `memory/personal_memory.sqlite3`, `memory/long_term.json`, `memory/abubakar_profile.md` | SQLite + markdown |
| Provider-independent | complete | as above | not keyed to any model ✔ |
| Conversation history | complete | `chat_history/`, `chat_history_manager.py` | files |
| Task/event history | partial | `workspace_store.py` | UI-scoped |
| Retrieval | partial | `recall_chat_history` tool | no embeddings; substring/history scan |
| Long-term context | partial | profile + memory facts injected into prompt | manual sizing |
| Structured metadata | partial | SQLite schema | — |
| Obsidian integration | complete | exporter module | writes markdown + backlinks |
| Incremental capture | partial | `save_memory` + attention monitor | — |
| Raw records preserved | complete | chat history independent of summaries ✔ | — |
| Backup/recovery | partial | `backup/` tarballs | not automated |

**Risk noted:** `memory/personal_memory.sqlite3` is tracked in git (SECURITY S-6). It was
not modified or migrated.

## 3.4 Provider routing

| Feature | Status | Files | Gap |
|---|---|---|---|
| Provider-independent interface | partial | `grok_client.py`, `groq_client.py`, per-tool requests | no single adapter contract |
| Multiple adapters | partial | OpenRouter/Groq/Gemini paths exist | ad-hoc per module |
| Free-first routing | partial | config-driven | no quota awareness |
| Quota / rate-limit awareness | **missing** | — | — |
| Provider health | missing | — | — |
| Fallback routing | partial | TTS has a 4-tier chain | **LLM calls have none** |
| Timeout handling | partial | per-call timeouts | inconsistent |
| Error normalisation | missing | — | — |
| Model capability metadata | missing | — | — |
| Configurable model | complete | `config/api_keys.json`, `LIVE_MODEL` | — |
| Credentials outside source | complete ✔ | `config/`, `~/.hermes/.env` | not in code |
| Local-inference compatible | complete (interface) | adapter boundary | no local model installed |

**Recommendation:** LiteLLM as a library behind a new `core/providers.py` — it closes
fallback, normalisation, quota and capability-metadata gaps in one dependency.

## 3.5 Browser and PC automation

| Feature | Status | Files | Evidence |
|---|---|---|---|
| Browser automation | present-unverified | `actions/browser_control.py`, `browser.py`, Playwright | 18 actions declared |
| Page inspection | present-unverified | `get_text`, snapshot helpers | — |
| Navigation | present-unverified | `go_to`/`back`/`forward`/`refresh` | — |
| Form interaction | present-unverified | `fill_form` (now consequential) | — |
| Downloads | present-unverified | `actions/url_downloader.py` | — |
| File interaction | complete | `actions/file_controller.py` | heavily exercised by tests |
| PC automation | present-unverified | `desktop_input.py`, `computer_control` | — |
| Screen observation | **broken/unknown** | screenshot helpers | reported "poor screen capture" |
| Action verification | missing | — | no post-condition check |
| Error reporting | partial | `error_logger.py` | — |
| Recovery from failure | missing | — | no retry/rollback |

Reported complaints (clicks/typing errors, capture, display handling, fullscreen, desktop
display) are **not resolved** by this audit. Playwright is not importable from the system
interpreter — only from `venv/` — which alone explains several failures in scripts that
shell out to `python3`.

## 3.6 Research and information

| Feature | Status | Files |
|---|---|---|
| Web research | complete | `web_search` tool |
| Source collection / citation | partial | prompt-level |
| Summarisation | complete | `youtube_video`, research agent |
| Real-time news | partial | `web_search` + `weather_report` |
| Knowledge organisation | partial | memory + Obsidian |
| **God's Eye View** | **complete, running** | `helix/ui/` + `helix-globe.service` + upstream `gods-eye-view/` |
| **Books of Eras** | **complete, preserved** | `helix/tools/eras.py` (38,111 B) — untouched; a stray identical copy in `JARVIS/tools/` was removed |

Both named HELIX features were preserved. `eras.py` was verified byte-identical between the
two locations before the duplicate was removed.

## 3.7 Coding and technical assistance

| Feature | Status | Files |
|---|---|---|
| Coding assistance | complete | `agent/code_agent.py` |
| Repository inspection | complete | `file_controller`, `cmd_control` |
| Code analysis / debugging | partial | code agent + error logger |
| Dev task execution | partial | agent runtime |
| File editing under permission | partial | `file_controller` writes are `local-write`, deletes now `consequential` |
| Test execution | complete | `cmd_control` (consequential tier) |
| Git inspection | complete | `cmd_control` |
| Technical research | complete | `web_search`, research agent |
| PC/software tutor | complete | `agents/pc.md` + `agent/pc_agent` |

## 3.8 Hermes integration

| Aspect | Status | Evidence |
|---|---|---|
| Installation / runtime | complete | `.hermes/hermes-agent` @ `bf0203a794`, 20,799 tracked |
| Gateway | running | `hermes-gateway.service` |
| Skills | present | `~/.hermes` tree |
| Tool registration | complete | Hermes owns its own registry |
| Agent communication | partial | kanban/state DBs read by both bridges |
| Dependencies on JARVIS/HELIX | none inbound | Hermes does not import either ✔ |
| Duplicate functionality | **yes** — memory, task queue, messaging overlap | see DEAD_CODE report |
| Security | inherits `~/.hermes/.env` | not modified |
| Memory/data ownership | Hermes owns `~/.hermes/*.db` | untouched |

**Not reinstalled, not reconfigured.** ✔

## 3.9 LMS (planned, deferred)

| Capability | Status | Evidence |
|---|---|---|
| Course listing | partial | `tools/lms_client.py` (untracked, password login) |
| Content / resource retrieval | partial | same |
| Assignment info | partial | read path present |
| Quiz info | partial | read path present |
| Grades | partial | read path present |
| Teacher / forum info | partial | token inventory confirms write endpoints exist on the site |
| Calendar / events | **broken at source** | LMS returns `invalidparameter` for course-calendar and popup notifications |
| File downloads | partial | present, **uncapped** |
| Uploads / submissions | **draft-only** | never submitted; correct default |
| Write approval | **missing** | `confirm.*` gated nothing (now replaced by `core/confirmation`) |
| Write audit | **missing** | now possible via `core/audit` |
| Secret handling | **unsafe** | password in env |

No LMS write was attempted, and no credentials were used in this audit.

## 3.10 Future capabilities (deferred, not implemented)

| Capability | Code still present? | Decision |
|---|---|---|
| Android / Brahma | **removed** (28 files, 1,426 LOC → backup) | rebuild from scratch when approved |
| Smart home | **removed** (12 files, 1,588 LOC → backup) | deferred |
| Robotics | none | deferred |
| Phone/OS integration | `connect-*` removed | deferred |
| Windows/macOS/iOS | none | deferred |
| Local LLM inference | none | interface preserved |
| Extra connectors | `plugins/` | extension point |

---

# Reverse map: module → feature

| Module | Supports | Classification |
|---|---|---|
| `core/capabilities.py` | permission model | necessary infrastructure (new) |
| `core/policy.py` | authorization | necessary infrastructure (new) |
| `core/confirmation.py` | human approval | necessary infrastructure (new) |
| `core/audit.py` | audit logging | necessary infrastructure (new) |
| `core/voice.py` | shared voice | shared service (new) |
| `agent/planner.py` | orchestration | approved capability |
| `agent/executor.py` | tool execution + policy gate | approved capability |
| `agent/runtime.py` | task lifecycle (partial) | approved capability |
| `agent/helix_manager.py` | JARVIS↔HELIX delegation | approved capability |
| `actions/*` | 25 capabilities | approved capabilities |
| `bridge_ws.py` | remote control, TTS, LMS panel | necessary infrastructure |
| `dashboard/server.py` | mobile/dashboard | necessary infrastructure |
| `command_center.py`, `command_panels.py` | UI | UI |
| `workspace_store.py` | task/workspace state | necessary infrastructure |
| `error_logger.py` | observability | necessary infrastructure |
| `plugin_manager.py`, `plugins/` | extension point | reusable utility |
| `tools/lms_client.py` | LMS | deferred capability |
| `tools/live_tts.py` | TTS tier for the bridge | necessary infrastructure |
| `tools/check-*.py`, `shot-url.py` | diagnostics | development support |
| `gods-eye-view/` | globe rendering | upstream dependency |
| `helix/tools/eras.py` | Books of Eras | approved capability |
| `helix/tools/selfcheck.py` | diagnostics | development support |
| `backup/removed-20261106/` | recovery of removed features | archive |
