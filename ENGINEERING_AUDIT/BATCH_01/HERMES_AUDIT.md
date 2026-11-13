# Hermes Audit (Batch 01, partial)

## Version/runtime (VERIFIED)
- Hermes `v0.23.0 (2026.9.24)` stable, git install, Python 3.14.9, OpenAI SDK 2.54.0. Install: `/home/abubakargcx/.hermes/hermes-agent`. Config: `~/.hermes/config.yaml`. Env: `~/.hermes/.env`.
- Gateway running: PID 548124, `hermes ... gateway run`. WhatsApp bridge running: PID 548360, `whatsapp-bridge/bridge.js --port 3000 --session ~/.hermes/whatsapp/session --mode self-chat`. Supervisor present (548361).

## Provider/default config (VERIFIED)
- Effective default: `provider: openrouter`, `default/model: openrouter/auto` (no custom `base_url`/`api_mode` in active model block). Corrected in prior user-approved controlled change with timestamped backup preserved.
- `OPENROUTER_API_KEY` present (value not exposed). Other common provider keys absent in earlier redacted check (OBSERVED at that time). `providers:` block empty.

## Fallback/routing capability (OBSERVED from local code/docs)
- Hermes supports cross-provider fallback chains (`fallback_providers`, legacy `fallback_model`), `hermes fallback` CLI, credential pools, auxiliary fallback policies, reset-aware cooldown/retry behavior. Evidence: `fallback-providers.md`, `hermes_cli/fallback_config.py`, `agent/fallback_cooldown.py`, fallback tests. **Distinction:** `openrouter/auto` = OpenRouter-internal selection, not Hermes cross-provider failover.

## Honcho integration signals (OBSERVED, redacted)
- `~/.hermes/honcho.json` present: `HONCHO_BASE_URL=http://localhost:8123`, local environment, API key present (**redacted**). Hermes config/state includes Honcho-related artifacts (`honcho.json`, prior messages referenced Honcho plugin/command). Actual runtime read/write contract and canonical memory ownership **UNVERIFIED**.

## OmniRush (VERIFIED)
- Hermes-side OmniRush provider/aliases removed previously; OmniRush CLI/proxy/tokens preserved. Proxy healthy at 20129. Gateway `403 official_client_required` remains the blocker for third-party Hermes chat use (context).

## Skills/MCP/tools/sessions (UNVERIFIED/partial)
- Hermes has tool/skill/plugin architecture (install dir contains plugins/providers). Full skill registry, MCP integration, session persistence behavior, and Hermes↔JARVIS↔HELIX execution contracts not fully mapped in this pass.

## Risks/gaps
- Hermes gateway/bridge consume meaningful resources on constrained hardware. Historical concern: Hermes process “stopped/traced (T)” vs service active — not observed in this snapshot (current process state not deeply inspected). Fallback chain not configured; resilience depends on OpenRouter availability/credits. **RECOMMENDED (approval required):** design minimal fallback only after verifying credentials/capabilities and cost/limits.
