# GitHub Licence and Security Review

Rules applied: no code is copied without a verified licence; an absent licence is **not**
permission; no third-party MCP server is added to the runtime; nothing is cloned into
`AI_WORKSPACE`.

---

## 1. Licence matrix

| Repository | Licence (as published) | Verdict for this project |
|---|---|---|
| `snakers4/silero-vad` | **MIT** | ✔ Adopt as a dependency |
| `dscripka/openWakeWord` | **Apache-2.0** | ✔ Compatible; keep NOTICE if vendored |
| `KoljaB/RealtimeSTT` | **MIT** | ✔ Licence fine, ✘ Python <3.13 |
| `alesaccoia/VoiceStreamAI` | **MIT** | ✔ Patterns only |
| `wiseman/py-webrtcvad` | **not verified** | ⚠ Do not vendor until confirmed |
| `marklynd/mcp-approvals` | **MIT** | ✔ Pattern only |
| `byQuexo/agent-approval-gate` | **MIT** | ✘ Node/TS |
| `kingtutt52/Agentic-OPS` | **MIT** | ✘ Scope |
| `manyu-lnmiit/agent-checkpoint-runtime` | **MIT** | ⚠ 1 commit |
| `isaacuselman/agentckpt` | **MIT** | ⚠ 5 commits |
| `yinghang815-create/agent-checkpoint-sqlite` | **Apache-2.0** | ⚠ Unproven |
| `langchain-ai/langgraph` (checkpoint-sqlite) | **MIT** | ✘ Framework lock-in |
| `BerriAI/litellm` | **MIT** (docs; confirm `LICENSE` file before shipping) | ✔ Adopt as a library |
| `vahid8/llm-gateway` | **MIT** | ✔ Patterns only |
| `yolorouter/yolorouter` | **Apache-2.0** | ⚠ Extra binary |
| `ahwanulm/AmRouter` | **MIT** | ✘ Governance |
| `MrFadiAi/free-llm-gateway` | **MIT** | ✘ Governance |
| `adcwb/ai-gateway` | **MIT** | ✘ Scope |
| `QwenLM/open-computer-use` | **Apache-2.0** (+ MIT/MPL-2.0 components) | ⚠ Wayland unsupported |
| `microsoft/magentic-ui` | open source research prototype (verify `LICENSE`) | ✔ Patterns only |
| `coddingtonbear/obsidian-local-rest-api` | **MIT** | ✔ Read-only integration |
| `hexatester/moodlepy` | **MIT** | ✔ Candidate dependency |
| `mrcinv/moodle_api.py` | **MIT** | ✔ Patterns only |
| `Lamb-Project/moodle-cli` | **GPL-3.0** | ✘ **Copyleft — do not copy** |
| `joshuapare/moodle-api-gen` | **GPL-3.0** | ✘ Copyleft + unavailable plugin |
| `python-moodle` (PyPI) | **MIT** | ⚠ Password session model |
| `moodle-mcp-connector` (PyPI) | MIT (per its NOTICE) | ⚠ Needs server plugin |
| `cca/moodle-python-apis` | **none visible** | ✘ **No licence = no use** |

**Copyleft boundary:** GPL-3.0 Moodle tooling may be *read* for API shapes and must not be
copied into JARVIS or HELIX. Both projects are currently unlicensed/private; vendoring GPL
would force the whole distribution to GPL.

## 2. Supply-chain findings

| Risk | Repo / component | Detail |
|---|---|---|
| **ToS violation + credential automation** | AmRouter | Automates provider account creation with Playwright, 2Captcha and temp-mail. Would put the owner's identity behind an automated sign-up. **Blocked.** |
| **Grey-market free tiers** | free-llm-gateway | Aggregates "free" keys that violate provider terms and vanish without notice. **Blocked.** |
| **Vault write = RCE** | obsidian-local-rest-api | Documented by the plugin itself: writing into `.obsidian/` executes `main.js` on next load; reading it leaks the plugin's API key. **Read-only integration only, path-guarded.** |
| **Brand-new code with security claims** | mcp-approvals (7 commits), agent-checkpoint-runtime (1 commit), agentckpt (5 commits) | Too new to depend on for an approval gate. Pattern donors, not dependencies. |
| **Unpinned transitive surface** | `litellm` | Large dependency tree; pin exactly and review the lock. |
| **Native binding** | py-webrtcvad | C extension, unverified licence, prebuilt wheels. Prefer Silero. |
| **Framework lock-in** | LangGraph / CrewAI / AutoGen | Adopting one makes the whole runtime its host. Rejected on architecture, also a supply-chain concentration. |

## 3. Security posture of the *our-side* integration points

| Our surface | Exposure | Mitigation in place | Remaining |
|---|---|---|---|
| `bridge_ws.py` | `127.0.0.1:8875`, CORS `*` | loopback bind | origin allowlist + session token |
| `live_server.py` (HELIX) | `127.0.0.1:8788` | loopback bind, key never sent to browser | per-connection auth |
| `core/audit.py` | writes personal action data | `0600`, redaction, XDG dir | rotate/expire |
| `core/confirmation.py` | in-process tokens | single-use, TTL, payload-bound | **needs wiring on live chain** |
| `tools/lms_client.py` | password in env | none | token auth, download cap |
| `backup/removed-20261106/` | **contains `smart_home.key` and paired-device records** | out of the running tree | treat as sensitive; encrypt or delete after the rollback window |

## 4. Dependency verification commands used

```
git ls-files | grep -iE "api_keys|\.env|secret|token|credential|\.key$|\.sqlite3$"
git grep -nIE "(api_key|password|token)\s*=\s*[\"'][A-Za-z0-9_-]{16,}"
```

Result: **no secrets in either repository.** One user database
(`memory/personal_memory.sqlite3`) is tracked — see SECURITY S-6.

## 5. Adoption conditions

Any candidate that becomes a dependency must meet all of:

1. A licence file present in the repo and compatible with private use.
2. Pinned version + hash in `requirements.txt`.
3. No network listener started on our behalf without explicit configuration.
4. No credential handling that bypasses `core/voice.read_gemini_key` or the config store.
5. Reviewed for `eval`/`exec`/`subprocess` on untrusted input.
6. Removable: an adapter boundary so it can be swapped without touching `agent/`.
