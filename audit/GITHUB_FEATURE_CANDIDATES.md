# GitHub Feature Candidates

Feature-by-feature comparison of what exists in the workspace against what open source
offers. `ours` = already implemented here. Nothing below was installed.

---

## 1. Master comparison

| Feature | Ours today | Candidate | Licence | Fit | Recommendation |
|---|---|---|---|---|---|
| VAD | none | silero-vad | MIT | CPU, <1 ms/frame, pip | **Reuse (adopt)** |
| Wake word | prompt-only | openWakeWord | Apache-2.0 | 16 kHz PCM, ONNX | **Integrate via adapter** |
| Streaming STT | model-side | RealtimeSTT | MIT | **Python <3.13; we run 3.14** | **Reject (incompatible)** |
| WS STT server pattern | HELIX proxy | VoiceStreamAI | MIT | same architecture | **Borrow pattern only** |
| TTS | 4-tier chain | edge-tts, Piper | already used | working | **Keep ours** |
| Shared voice config | `core/voice.py` | — | — | new, ours | **Keep ours** |
| Approval gate | `core/confirmation.py` | mcp-approvals | MIT | 7 commits, MCP server | **Borrow pattern only** |
| Approval UX | CLI/UI confirm | Magentic-UI action guards | research | toggles co-plan/co-task | **Borrow pattern** |
| Audit log | `core/audit.py` JSONL | Agentic-OPS hash chain | MIT | whole framework | **Reject; optionally hash-chain ours** |
| Capability registry | `core/capabilities.py` | none needed | — | ours is 150 lines | **Keep ours** |
| Durable tasks | none | agentckpt / DBOS | MIT / — | SQLite, in-process | **Investigate (DBOS first)** |
| Provider fallback | TTS only | LiteLLM (library) | MIT | 100+ providers, SDK mode | **Reuse (adopt)** |
| Provider gateway service | none | llm-gateway, yolorouter | MIT / Apache-2.0 | extra process | **Reject for now** |
| Free-tier aggregation | none | free-llm-gateway | MIT | scrapes free tiers | **Reject (governance)** |
| Auto account creation | none | AmRouter | MIT | CAPTCHA solving | **Reject (ToS/supply chain)** |
| Browser automation | Playwright in venv | — | — | ours exists | **Repair ours** |
| Desktop / computer use | `desktop_input.py` | QwenLM/open-computer-use | Apache-2.0 | **X11/XWayland only, no native Wayland** | **Investigate after display check** |
| Screen capture | screenshot helpers | — | — | reported broken | **Repair ours** |
| Memory store | SQLite + markdown | — | — | ours is provider-independent | **Keep ours** |
| Obsidian bridge | markdown exporter | obsidian-local-rest-api | MIT | REST + MCP, RCE risk if writing `.obsidian/` | **Integrate read-only** |
| Research agents | `agent/research_agent.py` | — | — | ours | **Keep ours** |
| Coding agent | `agent/code_agent.py` | — | — | ours | **Keep ours** |
| Orchestration framework | `agent/` custom | LangGraph/CrewAI/AutoGen | MIT | would replace ours | **Reject (monolith decision)** |
| Hermes skills | installed | NousResearch/hermes-agent | upstream | running | **Keep, extend** |
| Moodle client | `lms_client.py` (password) | moodlepy | MIT | typed, 3.8+ | **Reuse or reimplement** |
| Moodle reference | — | mrcinv/moodle_api.py | MIT | 1 file | **Borrow pattern** |
| Moodle CLI/docs | — | Lamb-Project/moodle-cli | **GPL-3.0** | SSO/token notes | **Read only, never copy** |
| Moodle codegen | — | moodle-api-gen | **GPL-3.0** | needs unavailable plugin | **Reject** |
| Cross-platform desktop | Tkinter/Qt | — | — | ours | **Keep ours** |

## 2. Where the workspace already wins

Three things are better here than in any candidate I found:

1. **`core/confirmation.py`** — payload-bound, single-use, 300 s TTL, in-process. The
   open-source gates either live inside an MCP server (extra hop) or in TypeScript.
2. **`core/capabilities.py`** — tiered with per-action overrides and a `forbidden` tier for
   assessment-taking. No candidate models "this capability must never run".
3. **Provider-independent memory** — SQLite plus markdown, no vector DB, no vendor. Swapping
   models cannot destroy history.

## 3. Where the workspace is genuinely behind

| Gap | Impact | Cheapest fix |
|---|---|---|
| No VAD | model hears noise as a turn; costs latency and quota | Silero VAD (~1 file, MIT) |
| No LLM fallback | one provider outage stops the assistant | LiteLLM library |
| No durable task state | a crash loses the agent run | DBOS or a 200-line SQLite checkpoint |
| No test coverage in HELIX | regressions are invisible | pytest for `eras`/`bridge` first |
| Two dispatch chains | every tool change is a double edit | one guard at chain A |

## 4. Explicitly not adopted, with reasons

| Repo | Reason |
|---|---|
| LangGraph / CrewAI / AutoGen | Replacing `agent/` with a framework contradicts the modular-monolith decision and would discard working orchestration. |
| Agentic-OPS | Enterprise YAML workflow engine; far more surface than a single-user assistant needs. |
| AmRouter | Automates provider sign-up with Playwright + 2Captcha — ToS violation and supply-chain risk. |
| free-llm-gateway | Aggregates grey-market free tiers that break constantly. |
| RealtimeSTT | `Python <3.13`; environment is 3.14.4. |
| GPL Moodle clients | Copyleft would propagate into the project. |
| Unlicensed scripts (`cca/moodle-python-apis`) | No licence is not permission. |
| Any MCP server | Not added to the runtime, per the directive. |
