# HELIX Complete Audit

## 1. Shape of the system

HELIX is small: **18 Python files, 5,511 lines**, 72 tracked files. It is an orchestrator
plus a globe front-end, not a second assistant runtime.

```
helix/
├── tools/
│   ├── live_server.py      ← Gemini Live WebSocket proxy (127.0.0.1:8788)   [transport]
│   ├── live_tts.py         ← stateless text→WAV tier for /tts               [transport]
│   ├── helix_voice.py      ← phone-call bridge with create_task/recall      [transport]
│   ├── eras.py             ← Books of Eras
│   ├── selfcheck.py        ← environment/self diagnostics
│   ├── helix-call-server.py← call signalling around helix_voice
│   ├── oci-a1-launch.sh    ← always-free capacity hunter
│   └── (diagnostic scripts)
├── bridge/                 ← HTTP/WS bridge for the UI
├── ui/                     ← Vite globe (God's Eye View), 16 tracked source files
├── agents/                 ← agent persona files
├── docs/                   ← PROGRESS.md, AGENT_ARCHITECTURE.md, VOICE_AUDIO_DIAGNOSTIC.md
├── inbox/, logs/           ← runtime, untracked
```

## 2. Feature status

| Feature | Where | Status |
|---|---|---|
| God's Eye View globe | `ui/` + `helix-globe.service` (Vite) + `gods-eye-view/` upstream | **Present and running.** Consumes upstream repo; not vendored. |
| Books of Eras | `tools/eras.py` | **Present.** Kept untouched; not removed with the voice work. |
| Gemini Live voice proxy | `tools/live_server.py` | Present, running as `helix-live.service` |
| Stateless TTS tier | `tools/live_tts.py` | Present; used by the bridge `/tts` chain |
| Phone-call voice | `tools/helix_voice.py` + `helix-call-server.py` | Present |
| Task dispatch to agents | `helix_voice.build_tools` (`create_task`), bridge | Present, partial |
| Shared memory recall | `run_voice(on_recall=...)` | Present as a callback contract; provider depends on caller |
| Multi-agent orchestration | `agents/`, bridge queue | Partial — no durable task lifecycle |
| Self-diagnostics | `tools/selfcheck.py` | Present |

Nothing in this list was deleted. The only HELIX work was voice-configuration
consolidation (below).

## 3. What was actually wrong with HELIX's voice

Three modules each resolved the same three things independently:

| Module | Model | Voice | Key lookup |
|---|---|---|---|
| `live_server.py` | `HELIX_LIVE_MODEL` or `gemini-3.8-live` | `HELIX_LIVE_VOICE` or `Charon` | own regex over `~/.hermes/.env` |
| `live_tts.py` | `HELIX_LIVE_MODEL` or `gemini-3.8-live` | argv | a **second copy** of the same regex |
| `helix_voice.py` | `HELIX_LIVE_MODEL` or `gemini-3.8-live` | default | a **third** resolver with a `/opt/helix-call/gemini.key` fallback |

Meanwhile JARVIS used `gemini-3.1-flash-live-preview`. So the two assistants were, by
default, configured to speak through **different models**, and HELIX carried three copies
of key parsing. `helix/docs/PROGRESS.md:3664` already recorded this as known duplication
and never fixed it.

## 4. What was done

| Change | Effect |
|---|---|
| `JARVIS/core/voice.py` created | Single definition of model, voice, wake phrases, persona, sample rates, key lookup |
| `live_server.py` imports the contract | Model/voice/persona/rates/key now come from JARVIS; HELIX keeps only the WebSocket transport and its own rider |
| `live_tts.py` imports the contract | Model, output rate and key come from JARVIS |
| `helix_voice.py` imports the contract | Model and key come from JARVIS; the `/opt/helix-call` key-file fallback is preserved through `read_gemini_key` |
| `tools/check-live.py` | Stale `gemini-3.8-live` default corrected |

`live_server.py` now **refuses to start** if it cannot import `core.voice` rather than
silently drifting back to its own copy:

```
HELIX requires the shared JARVIS voice core at .../JARVIS/core/voice.py (…).
Set JARVIS_ROOT to the JARVIS checkout.
```

This is deliberate. A fallback would re-create the divergence within a month.

### Why the three files were kept, not deleted

The directive says HELIX must not maintain a *separate independent voice core*, and that
unique useful behaviour must be migrated before removal. These three files are not cores:

- `live_server.py` is the only thing that can hold the API key outside the browser (Gemini
  Live has no direct browser WebRTC mode). Deleting it breaks the running service.
- `live_tts.py` is the stateless TTS tier the bridge `/tts` chain calls as a subprocess.
  Deleting it breaks `/tts`.
- `helix_voice.py` is imported by `tools/helix-call-server.py` (line 156).

They are **transports**: no persona of their own, no independent model choice, no
independent key policy. What made them a second core — duplicated configuration — is gone.
Deleting them instead would have been the "delete before tracing dependencies" mistake the
directive forbids, and I found the `helix-call-server.py` import only *because* I checked
references before removing.

## 5. Verification performed

| Check | Result |
|---|---|
| `python3 -m py_compile` on all three voice modules | pass |
| Import the shared contract from `helix/tools` | resolves to `gemini-3.1-flash-live-preview`, voice `Charon`, 720-char persona |
| Divergent model id left in `helix/tools/` | none |
| Two-client audio, barge-in, mic capture | **not tested** — needs a browser and an audio device |
| `helix-live.service` | still running. **It executes `~/helix/tools/live_server.py`, not this tree** — see §5.1 |

Honest statement: **the consolidation is verified structurally, not audibly.** No mic was
captured, no speaker monitored, no browser session opened.

### 5.1 The deployed copy is not this tree

`systemctl --user cat helix-live.service` returns:

```
ExecStart=/home/abubakargcx/.local/share/helix-live-venv/bin/python \
          /home/abubakargcx/helix/tools/live_server.py
```

That is **`~/helix`**, outside `AI_WORKSPACE`. The same is true of
`oci-a1-launch.service` (`%h/helix/tools/oci-a1-launch.sh`).

Consequences, stated plainly:

- Editing the workspace `helix/` does **not** change what the running service executes.
  "Takes effect on restart" is only true if `~/helix` is the same tree (symlink or
  bind-mount) rather than a second copy.
- Whether they are the same tree was checked by inode comparison during this audit; the
  result is recorded in the final report rather than assumed here.
- If they are separate, the shared-contract change must be applied to `~/helix` (or the
  service repointed) before any audible verification is meaningful.

## 6. Repo hygiene fixed

A broad `git add -A` during checkpointing had pulled **1,026 `ui/node_modules` files**
(three.js) and two user PDFs/screenshots into the HELIX index, taking tracked files from 71
to 1,098. Both were untracked and `.gitignore` extended:

```
ui/node_modules/
ui/.vite/
inbox/
```

Final: **72 tracked files**, working tree clean. This is the kind of change that would be
permanent if it were pushed; it was not pushed.

## 7. Known HELIX defects (not fixed)

| # | Defect | Note |
|---|---|---|
| H-1 | Voice verified only structurally | Needs the user to listen |
| H-2 | `bridge/server.py` deleted from working tree but tracked at checkpoint | Restored by the checkpoint commit; confirm it is the intended version |
| H-3 | Task lifecycle is fire-and-forget (`create_task` → queue) | No receipt, no retry, no dedupe |
| H-4 | `docs/PROGRESS.md` is 3,600+ lines of narrative | Useful history, poor documentation; fold into `docs/` |
| H-5 | No tests | 18 modules, zero test functions |

## 8. Verdict

HELIX's capabilities (globe, eras, call voice, dispatch) are intact. Its voice is no longer
a parallel universe — it is the JARVIS core plus three transports. It still has no tests,
which is the largest quality gap in the workspace after JARVIS's two voice defects.
