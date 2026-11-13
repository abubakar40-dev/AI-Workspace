# JARVIS Complete Audit

## 1. Shape of the system

JARVIS is a modular monolith with **two independent tool-dispatch paths** and one shared
model session.

```
main.py (3,621 lines)
├── startup: single-instance lock → UI → JarvisLive (Gemini Live session)
├── runner(): agent_runtime.start() + JarvisLive
├── JarvisLive
│   ├── microphone → 16 kHz PCM → Gemini Live (bidi session)
│   ├── audio_in_queue ← model audio → speaker (24 kHz)
│   ├── tool dispatch chain A  (async loop, `elif name == ...`)
│   └── speak / mute / interruption handling
└── bridge_ws.py (127.0.0.1:8875) → dashboard + mobile + LMS panel
agent/
├── planner.py    → PLANNER_PROMPT, tool list for the agent team
├── executor.py   → _call_tool(tool, parameters, speak)  [dispatch chain B]
└── runtime.py    → queue, worker, event subscription
actions/          → tool implementations
memory/           → personal_memory.sqlite3 + Obsidian export
```

Two dispatch chains is the single most important structural fact about JARVIS: a tool can
be declared once in `TOOL_DECLARATIONS` and still be unreachable from one of the two paths.
That is exactly what had happened to Brahma Connect and smart-home, and it is why removing
them required editing declarations, both chains, the voice router and startup.

## 2. Tool inventory (after cleanup)

25 declared capabilities remain. Before cleanup there were 32.

| Capability | Tier (new policy) | Dispatch A | Dispatch B | Notes |
|---|---|---|---|---|
| `open_app` | local-write | ✔ | ✔ | |
| `browser_control` | local-write (`fill_form` = consequential) | ✔ | ✔ | 18 actions |
| `file_controller` | local-write (`delete`/`chmod` = consequential) | ✔ | ✔ | device-share removed |
| `computer_settings` | local-write | ✔ | ✔ | |
| `computer_control` | consequential | ✔ | ✔ | input synthesis |
| `cmd_control` | consequential | ✔ | ✔ | arbitrary shell |
| `send_message` | consequential | ✔ | ✔ | |
| `reminder` | local-write | ✔ | ✔ | |
| `weather_report` | read | ✔ | ✔ | |
| `web_search` | read | ✔ | ✔ | |
| `youtube_video` | read | ✔ | ✔ | play/summarise |
| `flight_finder` | read | ✔ | ✔ | |
| `save_memory` | local-write | ✔ | ✔ | |
| `recall_chat_history` | read | ✔ | ✔ | |
| `agent_task` | local-write | ✔ | ✔ | delegates to `agent/` |
| `agent_cancel` | local-write | ✔ | ✔ | |
| `agent_status` | read | ✔ | ✔ | |
| `presentation_builder` | local-write | ✔ | ✔ | |
| `spreadsheet_builder` | local-write | ✔ | ✔ | |
| `word_document` | local-write | ✔ | ✔ | |
| `pdf_document` | local-write | ✔ | ✔ | |
| `file_processor` | read | ✔ | ✔ | |
| `url_downloader` | local-write | ✔ | ✔ | |
| `game_updater` | consequential (`install`/`update`) | ✔ | ✔ | |
| `shutdown_jarvis` | consequential | ✔ | ✔ | confirmation still via UI |

Removed in this pass: `smart_home_control`, `connect_list_devices`, `connect_get_device`,
`connect_get_capabilities`, `connect_execute`, `connect_pair_device`,
`connect_disconnect_device`.

## 3. Voice pipeline (JARVIS owns the core)

| Stage | Where | Status |
|---|---|---|
| Mic capture | `JarvisLive`, 16 kHz PCM16 mono | present |
| Model session | Gemini Live, `LIVE_MODEL = gemini-3.1-flash-live-preview` | present |
| Audio out | `audio_in_queue` → speaker at 24 kHz | present |
| Interruption | mic stays open while speaking; `interrupted` handled | present |
| Wake words | "jarvis", "hey jarvis", "wake up jarvis" in prompt/policy | present, model-side only |
| Push-to-talk | — | **absent** |
| Local STT/VAD | — | **absent** (STT is model-side transcription) |
| TTS fallback | `actions/attention_monitor` speech hooks + Edge TTS path | present, partial |

**Honest status: the pipeline is code-complete but not verified audible in this audit.**
No microphone was captured and no speaker was monitored. Two pre-existing tests that
assert the boot greeting and the audio-writer lock **fail** (see §6). Anyone claiming
"voice works" after this audit would be guessing.

The concrete defects that would make output unclear, late or inaudible, in order of
likelihood:

1. **Two writers to one session.** `_send_realtime` writes to the Live session without the
   `_session_write` lock the tests expect. Concurrent writes on a bidi socket produce
   dropped or reordered audio. This is the failing test `test_the_audio_writer_uses_the_lock`.
2. **Boot greeting path removed but still asserted.** `_speak_boot_greeting` is no longer
   in `main()`, so startup is silent where it used to speak. Failing test
   `test_boot_speaks_the_greeting_not_the_briefing`.
3. **Mic gating around TTS.** `set_speech_hooks` closes the mic while Edge TTS plays. That
   protects against feedback but is also the classic cause of "the assistant cannot be
   interrupted" if the window is too wide.
4. **Sample-rate mismatch risk.** 24 kHz is assumed on the receive side; a device that
   negotiates 48 kHz will sound fast and chipmunked.

These are diagnosed, not fixed. Fixing #1 and #2 is cheap and is the top priority in §H of
the final report.

## 4. Memory and knowledge

- `memory/personal_memory.sqlite3` — personal facts. **Tracked in git** (pre-existing;
  security finding S-6).
- `chat_history/` — conversation records, untracked.
- Obsidian export — writes markdown into a vault; backlinks produced by the exporter.
- Provider independence: memory is SQLite + files, **not** keyed to any model. ✔

No memory database was touched, migrated or deleted in this pass.

## 5. Agent team

`agent/planner.py` builds a plan from `PLANNER_PROMPT`; `agent/executor.py::_call_tool`
executes one step; `agent/runtime.py` runs a worker and publishes `submitted`/`progress`/
`complete` events that `main.py` renders in the Command Center.

New in this pass: `_call_tool` now evaluates `core.policy` and writes an audit line before
executing. That is the first place in either project where a tool call is classified and
recorded. It is the correct chokepoint for the agent path.

**It is not yet the chokepoint for the live Gemini path.** `main.py`'s dispatch chain A
still calls tool functions directly. Closing that gap is priority 2 in the final report.

## 6. Test results (executed, not assumed)

Command: `venv/bin/python -m pytest tests -q` in `JARVIS/`, Python 3.14.4.

| Run | Result |
|---|---|
| Baseline before changes | **509 passed, 2 failed** |
| After cleanup | **514 passed, 2 failed** (24.7 s) |

The same two tests fail before and after, so the cleanup neither caused nor fixed them:

- `tests/test_voice_fixes.py::test_boot_speaks_the_greeting_not_the_briefing` —
  asserts `_speak_boot_greeting` is called in `main()`; it is not.
- `tests/test_voice_fixes.py::test_the_audio_writer_uses_the_lock` — asserts
  `_session_write("send_realtime_input"` in `_send_realtime`; the lock is absent.

Net test count went 511 → 516: 6 Brahma tests removed, 11 `core/` tests added.

## 7. Defects found and fixed

| # | Defect | Fix |
|---|---|---|
| J-1 | Brahma Connect wired ahead of real tools in the voice router, so "open my phone" style phrases short-circuited normal dispatch for a feature with no paired device | Block, 6 tools, handler, voice router and startup all removed |
| J-2 | Smart-home redirect ran on **every** utterance before dispatch, importing a manager and listing devices even with zero devices configured | Redirect, tool, handler, service import and init removed |
| J-3 | `bridge_ws.py` inserted `"..", "tools"` on `sys.path` — one directory *above* the repo — so the LMS panel could never import `lms_client` | Path corrected to the repo's own `tools/` (L302) |
| J-4 | `confirm.request` / `confirm.response` existed in the bridge protocol but gated nothing | Replaced by `core/confirmation.py` (single-use, payload-bound, 300 s TTL) |
| J-5 | Two dispatch chains, no shared classification | `core/policy` + `core/audit` now run on the agent path |
| J-6 | `python-kasa` dependency with no remaining consumer | Removed from both requirement files |

## 8. Defects found and **not** fixed

| # | Defect | Severity | Why left |
|---|---|---|---|
| J-7 | Live dispatch chain A is not policy-gated | High | Needs a careful edit inside a 3,600-line async function; scheduled, not rushed |
| J-8 | `_send_realtime` writes without `_session_write` | High | Real concurrency fix; needs the lock contract understood |
| J-9 | Boot greeting no longer spoken | Medium | Behaviour decision for the owner |
| J-10 | `tools/lms_client.py` logs in with a stored **password**, and downloads are uncapped | High | The LMS workstream must replace this with token auth; see SECURITY S-2 |
| J-11 | `bridge_ws.py` sends `Access-Control-Allow-Origin: *` on a loopback service | Medium | Bound to 127.0.0.1, so not remotely reachable; still should be an allowlist |
| J-12 | Unpinned requirements | Medium | Pin after next clean install |
| J-13 | `browser_control` page/desktop reliability unverified | Unknown | Needs an interactive session on the real display |

## 9. Verdict

JARVIS is a real, working assistant with a large surface, one duplicated dispatch path and
two known voice defects. After this pass it is ~4,100 lines smaller, has one fewer
conceptual subsystem, and has a policy/audit/confirmation layer it did not have before.
It is not "done", and the two failing tests are the honest measure of that.
