# Hermes Inventory (live inspection, 2026-11-10)

**Scope:** `~/.hermes` (read-only inspection). No services restarted/killed; no secrets/config values printed.

## Runtime / service
- **systemd user service:** `hermes-gateway.service` (active, running). Exec: `.../.hermes/hermes-agent/.hermes/bin/hermes gateway run`, `WorkingDirectory=/home/abubakargcx/.hermes`, `HERMES_HOME=/home/abubakargcx/.hermes`, supervised child/restart policy configured. (from `systemctl --user cat hermes-gateway.service`)
- **Processes observed:** gateway Python process (`gateway run`, pid 548124 during inspection), WhatsApp bridge Node process (`scripts/whatsapp-bridge/bridge.js --port 3000 --session ~/.hermes/whatsapp/session --mode self-chat`, pid 548360), supervisor shell (`process_supervisor.sh`), Omnirush proxy Node process (`/tmp/omnirush-hermes/src/proxy.mjs`). Local listener: 127.0.0.1:33143 owned by hermes. `gateway.sock` present.
- **State files:** `gateway.lock`, `gateway.pid`, `gateway-starts.log`, `gateway-restart.log`, `gateway_state.json` (pid/kind/argv/platforms/session_store/code info/active work metadata), `channel_directory.json`.

## Configuration (existence/purpose only; values not recorded)
- `config.yaml` (top-level keys observed: runtime, attachments, plugins, model, kanban, cron, terminal, browser, tool_loop_guardrails, compression, prompt_caching, memory, sessions/streaming, skills, agent, database, etc.) with backups (`config.yaml.backup-*`). `.env`, `auth.json` (+ locks) present. `SOUL.md`, `.skills_prompt_snapshot.json`, `honcho.json`, `.auto_prune_*` present.

## Skills / plugins / tools
- `skills/` contains ~20 top-level entries plus bundled manifest/curator/usage/hub/locks metadata (`.bundled_manifest`, `.curator_*`, `.usage.json`, `.hub/`). Skills present include (sample): `apple`, `autonomous-ai-agents`, etc. (full enumeration pending deeper pass).
- `plugins/` includes `honcho` with install metadata.
- `tools/` includes bundled runtimes/binaries: Python 3.14.9, Node 26.12.1, npm, ffmpeg, ripgrep, Chromium, CUA driver, etc. `memories/` directory present.

## Sessions / data / logs
- `sessions/` request dumps and `sessions.json`. `kanban.db` (+ shm/wal/lock). `whatsapp/session` large (thousands of files). Logs: `agent.log`, `errors.log` (+ rotated), `gateway*`, `desktop*`, `whatsapp/bridge.log`, curator/update receipts/process-results, etc. `audio_cache/`, `image_cache/`, `cron/`, `backups/`, `bot_relay/`.

## Integration/communication picture (preliminary, VERIFICATION REQUIRED)
- Hermes runs as an independent local gateway/service with messaging bridge components (WhatsApp bridge present) and desktop/tooling assets. Actual AJ/JARVIS/HELIX call paths (imports, APIs/sockets/CLI/protocols, shared DBs) **not yet fully traced**; requires code/config/log-level evidence. No blind assumptions made.
- Risk notes: active service with locks/sockets/DB WAL; inspect-before-modify policy maintained.

## Gaps / next
- Enumerate skill metadata/permissions/dependencies; map plugin configs; identify exact health endpoints/protocols; trace AJ/JARVIS/HELIX ↔ Hermes integration points with concrete evidence; assess resource usage. Status: **PARTIAL / VERIFICATION REQUIRED**.

## Integration trace (2026-11-10, evidence-based)
- **AJ ↔ Hermes:** AJ defines a Hermes execution boundary/port (`aj/execution.py`: `UnavailableExecutionAdapter`, "NOT ATTACHED", requires GREEN SIGNAL), capability ownership/config flags (`hermes_endpoint`, `hermes_skills`, runtime none/hermes validation), orchestrator routing for HERMES-owned capabilities, and contract/docs/tests referencing Hermes. Runtime status evidence: `aj/runtime.py` reports attached `hermes: "NOT ATTACHED"`; capabilities show `hermes.execute_skill` planned/unavailable. **Classification:** contract/boundary implemented, **runtime NOT ATTACHED / dormant integration** (no live adapter wired).
- **JARVIS ↔ Hermes:** workspace-source scan (excluding .git/__pycache__/node_modules/.venv) found no concrete Hermes runtime integration points in `JARVIS/` (no direct references to `~/.hermes`, gateway socket, hermes CLI/service/protocol calls). **Classification:** no direct integration evidenced in source; **VERIFICATION REQUIRED** at runtime/config level.
- **HELIX ↔ Hermes:** same scan found no concrete Hermes runtime integration points in `helix/`. **Classification:** no direct integration evidenced in source; **VERIFICATION REQUIRED**.
- **Hermes → AJ/JARVIS/HELIX:** Hermes is an active independent gateway/service with skills/plugins/bridges; no evidence collected yet of it invoking AJ/JARVIS/HELIX control planes. **VERIFICATION REQUIRED** (needs protocol/log/config-level tracing).
- **Conclusion:** Current ecosystem shows AJ prepared for a future Hermes attachment but Hermes operates independently; cross-project orchestration/integration remains to be built and verified.

## Deeper evidence (2026-11-10 continuation, read-only)
- **Skills structure:** `~/.hermes/skills/` contains many skill directories with `SKILL.md` manifests (examples observed: `productivity/google-workspace/SKILL.md`, `email/himalaya`, `apple/*`, `research/*`, `autonomous-ai-agents/*`, etc.). Frontmatter/metadata commonly declares `name`, `description`, `version`, `platforms`, `required_credential_files`, and `metadata.hermes.tags/homepage/related_skills` plus setup/usage instructions and scripts (e.g. google-workspace has `scripts/setup.py`, `scripts/google_api.py` and references). **VERIFIED (structure/presence).** Actual runtime permission enforcement, sandboxing, invocation protocol, and per-skill test/health behavior **VERIFICATION REQUIRED**.
- **Gateway/config:** `config.yaml` includes sections for runtime, plugins, model, kanban, cron, terminal, browser, tool_loop_guardrails, compression, prompt_caching, memory, sessions/streaming, skills, agent, database (key names observed only). Gateway state/socket/lock/log/process evidence as previously recorded. **VERIFICATION REQUIRED** for callable protocol/API and health semantics beyond observed running state.
- **Integration conclusion unchanged:** AJ boundary is **implemented but NOT ATTACHED/dormant**; no direct runtime integration evidenced in `JARVIS/` or `helix/` source scans. Hermes is independent active infrastructure.
