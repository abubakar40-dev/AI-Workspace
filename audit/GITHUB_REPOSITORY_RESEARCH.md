# GitHub Repository Research

Feature-by-feature search for open-source code that could replace, repair or inform the
approved capabilities. Research only — **nothing here was installed, cloned or vendored.**

Candidate URLs and licences below were taken from repository metadata or vendor docs
during this session. Where a licence was not visible in the source I read, it is marked
**unverified** rather than guessed. Stars are deliberately omitted: they measure attention,
not suitability.

---

## 1. Voice: VAD, STT, wake word, audio pipeline

| Candidate | Purpose | Licence | Why it matters here |
|---|---|---|---|
| [snakers4/silero-vad](https://github.com/snakers4/silero-vad) | Pretrained VAD, ONNX or torch, CPU | **MIT** | Detects "did the user actually speak" in <1 ms per 30 ms frame on one CPU thread. Would fix the classic failure where the live session hears room noise as a turn. No key, no telemetry. |
| [dscripka/openWakeWord](https://github.com/dscripka/openWakeWord) | Wake-word detection, 16 kHz PCM | **Apache-2.0** | "Hey Jarvis" is currently enforced by *prompting the model*, which costs a full turn and can be ignored. This detects it before the session. Ships Silero VAD integration. |
| [KoljaB/RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) | STT + VAD + wake word in one library | **MIT** | Feature-complete, but declares `Python <3.13`; JARVIS runs **3.14.4**. **Not installable here** — pattern donor only. |
| [alesaccoia/VoiceStreamAI](https://github.com/alesaccoia/VoiceStreamAI) | WebSocket streaming STT server, faster-whisper + Silero | **MIT** | Shows the exact architecture HELIX already has (browser PCM over WS → server). Useful as a *reference* for its session isolation and VAD gating, not as a dependency. |
| [wiseman/py-webrtcvad](https://github.com/wiseman/py-webrtcvad) | WebRTC VAD binding | **unverified** | Works, but Silero is more accurate in noise. Only if a C extension is acceptable. |
| `parakeet-stream`, `realtime-mlx-stt` | Streaming ASR wrappers | MIT / — | Rejected: one is Apple-Silicon only, the other pins a CC-BY-4.0 model. |

**Verdict:** adopt **Silero VAD** (MIT, tiny, CPU-only) inside the shared voice core, and
evaluate **openWakeWord** for wake detection. Reject RealtimeSTT on the Python version, not
on quality.

## 2. Human-in-the-loop approval, policy, audit

| Candidate | Purpose | Licence | Assessment |
|---|---|---|---|
| [marklynd/mcp-approvals](https://github.com/marklynd/mcp-approvals) | Approval gate as an MCP server + hash-chained audit | **MIT** | Only 7 commits, created 2026-07. Its *reasoning* is the valuable part: "a decision is never overwritten" and "timeouts fail closed". Our `core/confirmation.py` already implements both. **Pattern donor.** |
| [byQuexo/agent-approval-gate](https://github.com/byQuexo/agent-approval-gate) | Gates every write/destructive tool call | **MIT** | TypeScript/Node. The classification idea (safe default: hold every write) matches our tier model. **Reject as code** (wrong language), borrow nothing we lack. |
| [OpenAI Agents SDK — HITL](https://openai.github.io/openai-agents-python/human_in_the_loop/) | Documented approval flow | Docs | Confirms the design choice that approvals must live **server-side** and survive a crash. |
| [kingtutt52/Agentic-OPS](https://github.com/kingtutt52/Agentic-OPS) | YAML workflows, hash-chained audit, HITL checkpoints | **MIT** | Large, claim-heavy, would replace our orchestration wholesale. **Reject** — violates "modular monolith, don't adopt a framework". |
| [manyu-lnmiit/agent-checkpoint-runtime](https://github.com/manyu-lnmiit/agent-checkpoint-runtime) | Durable execution + approval gates on SQLite | **MIT** | 1 commit. **Investigate later**, do not depend on it. |
| [isaacuselman/agentckpt](https://github.com/isaacuselman/agentckpt) | Checkpoint/recovery middleware | **MIT** | 5 commits, framework-agnostic, SQLite store. Small enough to read. **C — alternative** for task recovery. |
| [yinghang815-create/agent-checkpoint-sqlite](https://github.com/yinghang815-create/agent-checkpoint-sqlite) | Leases, fencing tokens, checkpoints | **Apache-2.0** | Fencing tokens solve duplicate-agent execution. Interesting, but unproven. **E.** |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-sqlite) | SQLite checkpointer | **MIT** | Only worth it if adopting LangGraph, which we are not. **Reject.** |

**Verdict:** build nothing new for approval — we already have it — and take *only* the
fencing-token idea when task recovery is implemented.

## 3. Provider routing and LLM gateway

| Candidate | Purpose | Licence | Assessment |
|---|---|---|---|
| [LiteLLM](https://docs.litellm.ai/docs/simple_proxy) | 100+ providers behind one OpenAI-compatible surface, fallbacks, budgets | **MIT** (docs; verify `LICENSE` before vendoring) | The strongest option. Use the **Python SDK**, not the proxy: one dependency, no extra service, and it gives error normalisation + fallback. **A — strong candidate.** |
| [vahid8/llm-gateway](https://github.com/vahid8/llm-gateway) | FastAPI gateway over LiteLLM with cost tracking | **MIT** | Shows a clean fallback-chain config. **B — pattern donor.** |
| [yolorouter/yolorouter](https://github.com/yolorouter/yolorouter) | Go gateway, key pools, failover | **Apache-2.0** | Another binary to run. **C.** |
| [ahwanulm/AmRouter](https://github.com/ahwanulm/AMRouter) | Gateway that **automates account creation** with Playwright + 2Captcha | **MIT** | **Reject.** Automating provider sign-ups with CAPTCHA solving is a terms-of-service and supply-chain risk, and it is exactly the kind of dependency this project should not carry. |
| [MrFadiAi/free-llm-gateway](https://github.com/MrFadiAi/free-llm-gateway) | Aggregates 14+ "free" providers | **MIT** | **Reject.** Free tiers scraped this way break constantly and often violate provider terms. "Free-first" must mean *legitimate* free tiers, not grey aggregation. |
| [adcwb/ai-gateway](https://github.com/adcwb/ai-gateway) | Go, virtual keys, quotas | **MIT** | Overkill. **D.** |

**Verdict:** adopt **LiteLLM as a library** behind our own adapter interface. It satisfies
"provider-independent, free-first, quota-aware, fallback" without a new service.

## 4. Browser and desktop automation

| Candidate | Purpose | Licence | Assessment |
|---|---|---|---|
| [QwenLM/open-computer-use](https://github.com/QwenLM/open-computer-use) | Native desktop driver (accessibility APIs) + browser-use | **Apache-2.0** (component MIT/MPL-2.0) | Real, maintained, cross-platform. **But:** Linux support is X11/XWayland only — **native Wayland is not supported**. This machine must be checked before anything is built on it. **B/E.** |
| Microsoft Magentic-UI ([repo](https://github.com/microsoft/magentic-ui), [paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/07/magentic-ui-report.pdf)) | Human-in-the-loop computer-use research UI | open source (research prototype) | Its **action guards** concept (auto-approve / co-plan / co-task toggles) is the right UX shape for our confirmation layer. **B — pattern donor.** |
| Playwright (already used) | Browser automation | Apache-2.0 | Already installed in `venv/`; the problem is reliability, not the library. |

**Verdict:** do not add a computer-use framework yet. First fix the three concrete
complaints (click/type failures, screen capture, fullscreen) against the existing
Playwright/CDP path, because they are diagnosed problems, not missing libraries.

## 5. Memory, knowledge, Obsidian

| Candidate | Purpose | Licence | Assessment |
|---|---|---|---|
| [coddingtonbear/obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api) | REST + MCP access to a vault | **MIT** | Would let memory writes go through Obsidian instead of file drops. **Read-only use only:** the plugin's own docs warn that writing into `.obsidian/` is effectively remote code execution, since Obsidian executes a plugin's `main.js`. |
| Obsidian itself | Knowledge layer | Proprietary (free to use) | Stays a *view* over memory, never the source of truth. That is already the design. |

**Verdict:** adopt the plugin for **read** (search, backlinks, list) behind an adapter that
refuses writes outside the vault's note directory. Keep SQLite authoritative.

## 6. LMS (Moodle) integration

NUML LMS2 is **Moodle 3.8.3+ (Build: 20200522)** with a token service that already exposes
`mod_assign_save_submission`, `mod_assign_submit_for_grading`, forum/message/calendar/grade
writes.

| Candidate | Licence | Assessment |
|---|---|---|
| [hexatester/moodlepy](https://github.com/hexatester/moodlepy) | **MIT** | Typed wrapper over the REST web service, Python 3.8+, tests present. Best fit for **token-based** access. **A/B.** |
| [mrcinv/moodle_api.py](https://github.com/mrcinv/moodle_api.py) | **MIT** | Single file, `call(function, **kwargs)`. Ideal as a *reference* for endpoint shapes; too thin to depend on (last meaningful activity 2016). **B.** |
| [Lamb-Project/moodle-cli](https://github.com/Lamb-Project/moodle-cli) | **GPL-3.0** | Good documentation of token/SSO realities (including that `/login/token.php` cannot work behind SSO). **Reject for code** — copyleft would infect the project. Read it, do not copy it. |
| [joshuapare/moodle-api-gen](https://github.com/joshuapare/moodle-api-gen) | **GPL-3.0** | Generated OpenAPI clients; requires a Catalyst REST plugin the LMS does not have. **D.** |
| [python-moodle](https://pypi.org/project/python-moodle) | **MIT** | Session/SSO automation with a password. Same credential model our audit rejects. **C.** |
| [moodle-mcp-connector](https://pypi.org/project/moodle-mcp-connector) | MIT (per its notice) | Depends on a server-side plugin that is disabled by default and not installed on NUML. **E.** |
| [cca/moodle-python-apis](https://github.com/cca/moodle-python-apis) | no licence visible | Example scripts, "not intended for production". **E** — unlicensed. |

**Verdict:** write a thin typed client in-house (~200 lines) modelled on `moodlepy`'s
function naming, or depend on `moodlepy` if it verifies against 3.8.3. Do **not** vendor
GPL code. Do **not** use password login.

## 7. Orchestration, coding agents, task scheduling

| Candidate | Note |
|---|---|
| LangGraph, CrewAI, AutoGen | Full frameworks. Adopting one would rewrite `agent/` for no capability we lack. **Reject** (modular monolith decision). |
| [DBOS + Pydantic AI](https://pydantic.dev/docs/ai/capabilities/durable_execution/dbos/) | In-process durable execution on SQLite/Postgres, `@DBOS.step`. The most credible "make `agent/` crash-safe" option. **B** — evaluate before building recovery by hand. |
| Hermes (`NousResearch/hermes-agent`) | Already installed and running. Skills are its extension point. **Keep, extend.** |

## 8. What this research concludes

Only **three** things are worth adopting now:

1. **Silero VAD** (MIT) inside the shared voice core.
2. **LiteLLM as a library** (MIT) behind our provider adapter.
3. **moodlepy or an in-house token client** (MIT) for LMS reads.

Everything else is either already built better in-house (`core/confirmation`), wrong for a
3.14/Python-modular-monolith environment (RealtimeSTT), or a governance risk
(CAPTCHA-solving routers, free-tier scrapers, GPL code).
