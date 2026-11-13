# Adoption Recommendations

The decision for each candidate, in the six categories the brief asks for, plus the order
to do them in. Nothing here is started in this pass.

---

## 1. Decisions

### Build ourselves
| Thing | Why |
|---|---|
| Capability registry | Done. 150 lines, models per-action risk and a `forbidden` tier no candidate has. |
| Confirmation tokens | Done. Payload-bound, single-use, in-process. Better than the MCP-server gates. |
| Audit log | Done. JSONL with redaction. Add hash-chaining only if tamper-evidence is ever needed. |
| LMS client | A thin typed token client (~200 lines) beats a GPL CLI or a password-session library. |
| Task recovery | Start with a SQLite table (`run_id, step, status, payload, updated_at`). DBOS only if that proves insufficient. |

### Reuse existing code (add as a dependency)
| Thing | Repo | Licence | Why now |
|---|---|---|---|
| VAD | `snakers4/silero-vad` | MIT | Fixes "model answers room noise"; CPU-only, <1 ms/frame |
| Provider routing | `BerriAI/litellm` (library mode) | MIT | Closes fallback, error normalisation, quota and capability metadata in one dependency |
| Moodle reads | `hexatester/moodlepy` | MIT | Typed token client, 3.8+ — or use it as the spec for our own |

### Integrate through an adapter
| Thing | Repo | Adapter boundary |
|---|---|---|
| Wake word | `dscripka/openWakeWord` | `core/voice.wake_detector` → returns bool; no session code inside |
| Obsidian | `coddingtonbear/obsidian-local-rest-api` | `memory/obsidian.py`, **read paths only**, refuse `.obsidian/` |
| Desktop automation | `QwenLM/open-computer-use` | only after confirming the display server is X11/XWayland |

### Borrow an architectural pattern (no code)
| From | Pattern |
|---|---|
| `marklynd/mcp-approvals` | "A decision is never overwritten" and "timeouts fail closed" |
| Microsoft Magentic-UI | Action guards: auto-approve / co-plan / co-task toggles |
| `OpenAI Agents SDK` HITL docs | Approval state lives server-side and survives a crash |
| `alesaccoia/VoiceStreamAI` | Per-session STT isolation, VAD-gated chunking |
| `vahid8/llm-gateway` | Ordered fallback chains per model, not per provider |

### Reject
| Repo | Reason |
|---|---|
| `AmRouter` | Automates provider sign-up with CAPTCHA solving — ToS and supply-chain risk |
| `free-llm-gateway` | Grey-market free tiers |
| `Lamb-Project/moodle-cli` | GPL-3.0 — would infect the project |
| `joshuapare/moodle-api-gen` | GPL-3.0 + needs a plugin the LMS does not have |
| `cca/moodle-python-apis` | No licence |
| `Agentic-OPS` | Enterprise framework; would replace our orchestrator |
| LangGraph / CrewAI / AutoGen | Framework lock-in contradicts the modular-monolith decision |
| `adcwb/ai-gateway`, `yolorouter` | Another service to run for no capability we lack |
| `RealtimeSTT` | Python <3.13; environment is 3.14.4 |
| Any MCP server in the runtime | Directive: no unreviewed third-party MCP servers |

### Defer
| Thing | Until |
|---|---|
| `DBOS` / `agentckpt` / `agent-checkpoint-sqlite` | after a hand-rolled SQLite step table proves too thin |
| `open-computer-use` | after the Wayland/X11 question is settled |
| Books of Eras extensions | untouched feature; not in scope |
| Android rebuild, smart home, robotics | explicitly deferred by the owner |

## 2. Feature-by-feature recommendation

| Feature | Decision |
|---|---|
| Voice capture / playback | **Repair ours** (session lock, boot greeting) |
| Voice activity detection | **Reuse** Silero VAD |
| Wake word | **Adapter** over openWakeWord |
| STT | **Keep ours** (model-side) |
| TTS | **Keep ours** (4-tier chain already works) |
| Shared voice contract | **Keep ours** (done) |
| Orchestration | **Keep ours**; add a policy guard to chain A |
| Task durability | **Build** a small SQLite checkpoint table |
| Permissions | **Keep ours** (done) |
| Audit | **Keep ours**; hash-chain only if needed |
| Provider routing | **Reuse** LiteLLM as a library |
| Memory | **Keep ours** (provider-independent) |
| Obsidian | **Adapter**, read-only |
| Browser automation | **Repair ours** |
| Screen capture | **Repair ours** |
| Desktop automation | **Investigate** after display check |
| Research / coding agents | **Keep ours** |
| Hermes | **Keep**, extend via skills |
| LMS reads | **Reuse/adapt** moodlepy |
| LMS writes | **Build** on `core/confirmation`; nothing exists to reuse safely |

## 3. Do-these-first order

1. **Fix the two failing voice tests.** They encode real defects (unlocked session writes,
   silent boot). Cheap, and they unblock any claim that voice works.
2. **Gate `main.py`'s live dispatch chain** with `core.policy`. One call site; closes the
   bypass that currently makes the permission layer half-real.
3. **Add Silero VAD** to the shared core. Removes a whole class of "it answered nothing".
4. **Adopt LiteLLM behind `core/providers.py`.** Fallback and normalisation stop being
   per-module improvisation.
5. **Point `helix-live.service` at the workspace tree** (or apply the same change to
   `~/helix`), then listen to it. Voice consolidation is unverified until then.
6. **Replace the LMS password client** with a token client, reads only, `quiz_attempt`
   registered `forbidden`.
7. **Pin `requirements.txt`.** Everything above is unreproducible without it.

## 4. What would make this advice wrong

- If the Pi/box running HELIX cannot import from a sibling JARVIS checkout, the shared
  contract needs a small installed package. Fix: `pip install -e JARVIS` or a vendored copy
  with a version check — not a silent fallback.
- If the display is native Wayland, `open-computer-use` is out and the existing Playwright
  path is the only option.
- If Moodle 3.8.3's token service lacks a function `moodlepy` assumes, the in-house client
  is the answer. Verify function-by-function before writing either.
