# Build One Assistant — Copy/Paste Recipe

The short version. Full detail in `AGENT_ARCHITECTURE.md`.

---

## 1. Create the profile

```bash
hermes profile create <id> --clone      # clones model/tools/env from the source profile
```

`<id>` is the Hermes profile id. It becomes:
- the Kanban `assignee` value
- the `state.db` directory name
- the UI agent id (after `ui_agent()` translation for `default`/`document`/`comm`)

---

## 2. Write the persona

`~/.hermes/profiles/<id>/SOUL.md` — one paragraph, plain markdown.

```markdown
You are <NAME>, the <ROLE> agent for <DOMAIN>.

<What you do, in 2-4 sentences.>

<Hard rules. Be specific and testable:>
- Never claim success without verifying.
- Never <dangerous thing> without explicit confirmation.
- Always cite sources as plain-text URLs.
- If you cannot verify, say so plainly rather than guessing.
```

### The description matters

```bash
hermes profile describe <id>
```

Returns ONE line. The **kanban orchestrator uses this to route work** — a card
titled "research X" gets assigned to whoever's description says "research".

Real:
```
$ hermes profile describe research
Finds, reads and summarizes information from the web, papers and videos. Cites sources.
```

Write it so a router can match on it.

---

## 3. Set the capability boundary

`~/.hermes/profiles/<id>/config.yaml`:

```yaml
platform_toolsets:
  cli:
    - clarify          # ask the human a question
    - file             # read/write files
    - memory           # read/write memories
    - skills           # read the skill catalogue
    - todo             # task list
    # add what this agent genuinely needs:
    # - terminal        # run shell
    # - browser         # web
    # - vision          # images
    # - computer_use    # GUI automation
    # - code_execution  # run code
    # - delegation      # spawn more agents
```

**The tool list IS the assistant.** A `comm` agent without `terminal` can never
touch your disk, no matter what its SOUL.md says. Add tools only when needed —
each one is an attack surface and a way to get stuck.

---

## 4. Set the model and fallbacks

```yaml
model:
  default: openrouter/free
  provider: auto
  base_url: https://openrouter.ai/api/v1

fallback_providers:
  - {provider: openrouter, model: nvidia/nemotron-3-ultra-550b-a55b:free}
  - {provider: openrouter, model: openrouter/free}
  - {provider: ollama,      model: qwen2.5:3b, base_url: http://localhost:11434/v1}
```

The chain is tried in order when the primary fails. **The ollama tier is what
eats 2.3 GB of RAM** — it loads a model into RAM on first use. Keep it last, and
kill the server when you are not using it:

```bash
pkill -f "ollama serve"        # the API server itself
pkill -f "llama-server"         # the loaded model (this is the RAM hog)
```

If the container blocks `sudo`, you cannot kill the `ollama`-user processes
from inside it — the host has to do it.

---

## 5. Set the deny-list

```yaml
approvals:
  deny:
    - '*sudo *'
    - '*rm -rf*'
    - '*rm --recursive*'
    - '*dd if=*'
    - '*dd of=/dev/*'
    - '*mkfs*'
    - '*git push --force*'
    - '*git reset --hard*'
    - '*git clean -f*'
    - '*rm /etc/*'  '*rm /usr/*'  '*rm /bin/*'  '*rm /sbin/*'
    - '*rm ~/.ssh/*'  '*rm ~/.aws/*'
    - '*.ssh/id_rsa*'  '*.ssh/id_ed25519*'
    - '*.aws/credentials*'  '*credentials.json*'
```

`approvals.deny` is **not bypassable** — not by `--yolo`, not by
`approvals.mode: off`. Keep it even for the PC agent, which is the one that
actually needs `terminal` and `computer_use`.

---

## 6. Give it memory

`~/.hermes/profiles/<id>/memories/MEMORY.md` and `USER.md`.

Format: blocks separated by a line containing only `§`.

```markdown
Fact about the domain.
§
Operating rule the agent must follow.
§
Env quirk: <what is broken here and what to do instead>.
```

`USER.md` is facts about the human; `MEMORY.md` is domain knowledge + operating
rules. Real example from this box:

```
Env quirks: Vision tool cannot analyze images — no LLM provider configured;
always ask user to describe images in text. Nine specialist sub-agents each with
own tools and roles; delegate to them, don't do their work. Must verify before
reporting — sub-agent summaries are claims, not evidence. Delivery: put paths in
MEDIA: tag.
```

`memory_char_limit: 2200`, `user_char_limit: 1375` — these are small. Be ruthless
about what earns a slot.

---

## 7. Give it skills (optional)

A skill is a directory with a `SKILL.md`:

```
~/.hermes/skills/<category>/<skill>/SKILL.md
```

```markdown
---
name: <skill>
description: <one line — this is what the model matches on>
version: 1.0.0
metadata:
  hermes:
    tags: [a, b, c]
prerequisites:
  pip: [some-package]
---

# <Skill>

## When to Use
<the trigger conditions>

## Procedure
<numbered steps the model follows>
```

Skills are **documentation, not code**. The model reads them on demand. The
description is the only thing always in context, so write it for matching.

---

## 8. Make it reachable

### From another agent (the important one)

Put the card on the board and assign it:

```bash
hermes kanban create "Research: <topic>" \
  --body-file - --assignee <id> --workspace scratch
```

The **gateway** dispatches it. Without the gateway running, nothing happens:

```bash
hermes gateway run &
```

### From a human

```bash
hermes -p <id>                 # interactive
hermes -p <id> -z "do the thing"
```

### From a UI

Your bridge reads the board and pushes `agent.status` / `task.upsert` / `chat`.
Translate the profile id to your UI's id (`default`→`helix`, `document`→`files`,
`comm`→`comms`) or the UI shows "undefined".

### From a channel

`platform_toolsets.<platform>: [hermes-<platform>]` in config.yaml, and the
gateway owns the channel connection.

---

## 9. Verify it actually works

```bash
# 1. the profile exists
hermes profile list

# 2. it can answer
hermes -p <id> -z "reply with exactly OK"

# 3. it can take a card
hermes kanban create "test card for <id>" \
  --body-file - --assignee <id> --workspace scratch
hermes kanban list
#    → status should go ready → running → done within a minute
hermes kanban show <task-id>

# 4. the deny-list bites
hermes -p <id> -z "run: rm -rf /tmp/nothing"
#    → must be refused, not attempted

# 5. it has memory
hermes -p <id> -z "what do you know about me?"
#    → should reflect USER.md + Honcho representation
```

---

## 10. The full checklist

```
[ ] profile created            hermes profile create <id> --clone
[ ] SOUL.md written            persona + hard rules
[ ] profile describe set       one line, for the router
[ ] tool allowlist set         platform_toolsets.cli — minimal
[ ] model + fallbacks set      model.default, fallback_providers
[ ] approvals.deny set         destructive patterns
[ ] memories/ written          MEMORY.md + USER.md
[ ] skills added (optional)     ~/.hermes/skills/<cat>/<name>/SKILL.md
[ ] gateway running            hermes gateway run
[ ] kanban initialised         hermes kanban init
[ ] verified end to end        a real card, claimed, completed, answered
```

---

## 11. If you want it to appear in the Helix UI

1. Add the profile id to `AGENT_IDS` in `bridge/bridge_ws.py`
2. Add it to `H.AGENTS` in `ui/src/js/00_core.js` with a name, role and pixel-art look
3. Add a desk for it in `ui/src/js/30_town.js` (`deskX` map) and a sprite
4. Rebuild: `cd ui && node build.js` (the bridge serves `ui/helix-ui.html`)
5. Restart the desktop app

The bridge derives the agent's state from the board automatically — no per-agent
code needed. It just needs to know the id.
