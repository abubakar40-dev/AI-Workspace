# Hermes → Honcho Controlled Validation (Workstream A)

**Date:** 2026-11-10. **Mode:** A1 read-only observation, A2 metadata-only. **No synthetic test initiated by Batch 06; no source/config/service/DB mutations.** Evidence includes new inspection of the plugin's declared hook and write gates.

## A1. Pre-test metadata snapshot (A2, no content)
| Metric | Value | Max created_at (metadata) |
|---|---:|---|
| workspaces | 2 | 2026-11-09 23:10:54.276904 |
| sessions | 1 | 2026-11-09 23:13:12.374012 |
| peers | 0 | — |
| messages | 0 | — |
| conclusions | 0 | — |

**Runtime state (observed):** Hermes gateway PID 548124; Honcho server PID 893598 (`honcho_local/honcho_server.py`, 127.0.0.1:8123); WhatsApp bridge 548360 (3000); OmniRush 918166; helix-live 10326; legacy-printer-app 973. Honcho plugin present at `~/.hermes/plugins/honcho` and enabled (`plugins.enabled: [honcho]`).

## A2. Plugin mechanics / write gates (new STATIC EVIDENCE)
| Fact | Evidence | Consequence for testing |
|---|---|---|
| Integration type | `plugin.yaml`: `hooks: [on_session_end]`; `register()` calls `ctx.register_memory_provider(HonchoMemoryProvider(...))` | Writes are driven by Hermes' memory-provider lifecycle + **session-end** hook, **not** by the model itself |
| Message persistence default | `config_schema.py`: `saveMessages` default **`true`** | Persistence is **enabled by default**; a successful session would write |
| Flush cadence | `writeFrequency` default **`async`** | Writes flush asynchronously → a delta may appear **after** the turn returns; any test must wait/poll |
| Identity | `honcho.json` contains only `HONCHO_BASE_URL=http://localhost:8123`, `HONCHO_API_KEY` (redacted), `HONCHO_ENVIRONMENT=local`; no `saveMessages`/`pinUserPeer` overrides | Defaults apply |
| Client config | `~/.hermes/honcho.json` (no peer pinning) | Peer/workspace naming derived at runtime — peer count currently 0, so no peer has been created yet |
| Test coverage of the write path | `tests/test_async_memory.py`, `tests/test_turn_author_peers.py`, `tests/test_honcho_startup_fail_open.py` (incl. `test_honcho_sync_turn_skips_write_when_save_messages_is_disabled`) | Plugin logic is unit-tested upstream; **runtime activation in this install is still unproven** |

## A3. Observed runtime event (pre-existing synthetic log content; NOT initiated by Batch 06)
Gateway/agent logs: `2026-11-10 00:25:38,370` local inbound `msg='Reply with exactly: HONCHO_TEST_OK'` (session `local-6e2f8a10…`). Agent log for that turn: `provider=custom base_url=http://localhost:8123 model=gpt-6-astra`, then `Streaming failed before delivery: 404 {'detail': 'Not Found'}` on `/chat/completions`. Honcho server log shows matching 404s (`/api/show`, `/chat/completions`) and contains no Honcho v3 write traffic for that window.

**Interpretation (EVIDENCE-ESTABLISHED):** the turn was **misrouted — Honcho's port was configured as the LLM provider endpoint**. The turn failed before a completed assistant response, so the `on_session_end`/`sync_turn` write path had no completed turn to persist. This is **not** evidence about the writer either way.

## A4. Post-observation metadata
Counts unchanged: `2 / 1 / 0 / 0 / 0`. No workspace, session, peer, message or conclusion delta; no new timestamps.

## A5. Is a compliant test constructible right now? (new, decisive)
A valid test needs **one completed Hermes turn** (user message + assistant response) on a correctly routed provider, because the write path is session-end/sync-turn based.

| Prerequisite | State | Result |
|---|---|---|
| Local zero-cost model available | **None**: no listener on 11434/1234/8080/5000; `ollama` CLI present but server not running (`could not connect to ollama server`) | **Unavailable** |
| Zero-cost provider otherwise | Only configured provider is `openrouter` (`model.provider: openrouter`, `model.default: openrouter/auto`) | Would be a **paid API call — prohibited** |
| Per-run override without config mutation | `hermes chat` supports `--provider`, `--model`, `--base-url`, `--api-key` (launch-scoped, not persisted) | Mechanism exists, but **no zero-cost backend exists to point it at** |
| Residual DB records | `saveMessages` default true; no documented, test-scoped cleanup tool inspected | Test **would create** workspace/session/peer/message rows (documentable, but irreversible without destructive cleanup that is prohibited) |

**Conclusion:** the test cannot be executed within Batch 06's constraints (no paid calls, no config/service changes, no destructive DB cleanup) **without first standing up a local model server**, which is itself a service/config change requiring approval. Stopping here rather than improvising is the instructed behaviour.

## Classification
**`TEST INCONCLUSIVE` / `PARTIALLY VERIFIED (static capability only)`**
- **EVIDENCE-ESTABLISHED:** plugin installed, enabled, registered as memory provider with `on_session_end` hook; persistence defaults on (`saveMessages=true`, `writeFrequency=async`); Honcho backend healthy; **0** messages/conclusions; an observed synthetic turn was misrouted to Honcho as LLM base URL and 404'd; no local zero-cost model exists to run a compliant test.
- **`RUNTIME WRITER VERIFIED`:** No. **`RUNTIME WRITER DISPROVEN`:** No (no valid turn ever completed).
- **Confidence:** High that the writer path is untested in this install; High that current 0-message state is explained by no completed turn; Low on actual post-turn write behaviour.

## Test recipe for the approval-gated phase (not executed)
1. Approval to start a **local** OpenAI-compatible model (e.g. ollama) or explicit authorization for a single minimal OpenRouter call.
2. Synthetic identity/session only (`b06-validation-*`), one turn, no personal content.
3. Pre/post A2 counts + `max(created_at)`; poll for `writeFrequency=async` flush; correlate Honcho request log (method/path/status only).
4. Record residual synthetic rows explicitly; no deletion without a documented safe mechanism.
5. Classify `RUNTIME WRITER VERIFIED / DISPROVEN / PARTIALLY VERIFIED / INCONCLUSIVE`.
