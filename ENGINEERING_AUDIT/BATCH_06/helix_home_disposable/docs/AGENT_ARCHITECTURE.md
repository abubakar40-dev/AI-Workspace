# HELIX / Hermes Agent Architecture — Complete Reference

Everything below was read off the running system, not inferred. Paths, config keys and
DB tables are the real ones.

---

## 0. The one-paragraph mental model

There is no "assistant code". An **assistant is a Hermes *profile*** — a directory
containing a persona (`SOUL.md`), a tool allowlist, a model, a private memory store, a
private session database, and a shared skill library. Nine of those directories plus
the `default` profile form the team. They collaborate through **one shared SQLite
board** (`~/.hermes/kanban.db`): the CEO writes a card, a named profile claims it,
works in its own isolated workspace, and writes the answer back onto the card. The
UI is a *viewer* on that board plus a WebSocket bridge that translates board changes
into events the front-end can animate.

```
                        ┌──────────────────────────────┐
   human ──chat/voice──▶│  HELIX desktop app (GTK3 +    │
                        │  WebKit2GTK)  ui/helix-ui.html│
                        └───────────────┬──────────────┘
                                        │  ws://127.0.0.1:<random>
                                        ▼
                        ┌──────────────────────────────┐
                        │  bridge/bridge_ws.py         │
                        │  reads board, emits events   │
                        └───────────────┬──────────────┘
                                        │ hermes kanban create
                                        ▼
   ┌────────────────────────────────────────────────────────────────┐
   │  ~/.hermes/kanban.db   (one shared board, all profiles)        │
   └───┬──────────┬──────────┬──────────┬───────────┬──────────────┘
       │          │          │          │           │
   ┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
   │default│  │research│  │  dev  │  │  pc   │  │ ...   │   ← each = 1 assistant
   │CEO    │  │Alice   │  │  Eve  │  │ Carol │  │       │
   └───┬───┘  └───┬───┘  └───┬───┘  └───┬───┘  └───┬───┘
       │          │          │          │          │
       └──────────┴──────┬───┴──────────┴──────────┘
                          │  each has its own
                          ├─ SOUL.md          persona
                          ├─ config.yaml      model + tools + guardrails
                          ├─ memories/        private notes
                          ├─ state.db         private sessions/messages
                          ├─ skills/          (shared library, per-profile symlink)
                          └─ workspace/       isolated scratch dir
```

---

## 1. Anatomy of ONE assistant (profile)

A profile is a directory. `~/.hermes/profiles/<id>/` contains:

| Path | What it is | Real example |
|---|---|---|
| `SOUL.md` | The persona. Prompt text the model always sees. | `pc/SOUL.md` → "PC-control agent. EXPLICIT confirmation before any destructive action…" |
| `config.yaml` | Model, tool allowlist, guardrails, fallbacks, approvals. | `pc/config.yaml` |
| `memories/` | `MEMORY.md` (notes) + `USER.md` (facts about the human). Plain markdown, `§`-separated. | `~/.hermes/memories/USER.md` holds "AbuBakar Ghafoor, BSSE 3rd sem…", "prefers Roman English/Urdu mix" |
| `state.db` | Private sessions, messages, tool calls, token usage. **Every profile has its own.** | `messages`, `sessions`, `gateway_routing` tables |
| `skills/` | The skill library (same set for all; shared source, per-profile view). | `apple, autonomous-ai-agents, creative, devops, education, email, media, note-taking, productivity, research, social-media, software-development, web` |
| `workspace/` | Isolated scratch directory for the agent's tasks. | `kanban/workspaces/<task-id>/` |
| `cron/` | Scheduled jobs owned by this profile. | `~/.hermes/cron/jobs.json` |
| `plugins/`, `hooks/`, `platforms/` | Plugin installs, event hooks, channel bindings. | |
| `profile.yaml` | Profile metadata (description, id). | |

### The `config.yaml` that defines the assistant

Real `pc/config.yaml`, abridged to the parts that matter (the CEO's own
`~/.hermes/config.yaml` is the same shape, but with the 8-tool CEO allowlist and
`kanban.dispatch_in_gateway: true` so the gateway does the dispatching):

```yaml
model:
  default: openrouter/free
  provider: auto
  base_url: https://openrouter.ai/api/v1

fallback_providers:            # tried in order when the primary fails
  - {provider: openrouter, model: nvidia/nemotron-3-ultra-550b-a55b:free}
  - {provider: openrouter, model: openrouter/free}
  - {provider: ollama,      model: qwen2.5:3b, base_url: http://localhost:11434/v1}

platform_toolsets:
  cli:                         # ← THE TOOL ALLOWLIST. This is the real difference
    - clarify
    - computer_use
    - file
    - memory
    - skills
    - terminal
    - todo
    - vision

approvals:
  deny:                        # never bypassable, not even --yolo
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

memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200
  user_char_limit: 1375
  nudge_interval: 10

agent:
  max_turns: 500
  reasoning_effort: medium

kanban:
  review_dispatch: true
  max_in_progress: 1
```

**Key insight:** the *tool allowlist* is the assistant's real capability boundary. A
`comm` agent that cannot see `terminal` can never touch your disk no matter what its
SOUL.md says.

The CEO (`default`) is deliberately trimmed to 8 tools — `clarify, delegation, file,
kanban, memory, skills, todo, web` — so that it **delegates** rather than doing the
work itself. The full builtin catalogue (`known_builtin_toolsets.cli`) is much
longer: browser, clarify, code_execution, computer_use, connections, context_engine,
cronjob, delegation, file, homeassistant, image_gen, kanban, memory, session_search,
skills, spotify, stt, terminal, todo, tts, video, video_gen, vision, web, x_search,
yuanbao. `platform_toolsets.cli` is the subset a given profile may use.

### The nine assistants, and what each may do

| Profile | UI name | Role | `platform_toolsets.cli` | Model | Fallbacks |
|---|---|---|---|---|---|
| `default` | HELIX | CEO / Orchestrator | clarify, delegation, file, kanban, memory, skills, todo, web | `nvidia/nemotron-3.5-lightning:free` | openrouter/free → … |
| `research` | Alice | Research | browser, clarify, connections, cronjob, delegation, file, memory, session_search, skills, todo, vision, web | `openrouter/free` | nemotron-3-ultra → openrouter/free → ollama qwen2.5:3b |
| `dev` | Eve | Development | browser, clarify, code_execution, file, memory, skills, terminal, todo | `openrouter/free` | same |
| `pc` | Carol | PC Control | clarify, computer_use, file, memory, skills, terminal, todo, vision | `openrouter/free` | same |
| `vision` | Dave | Vision | clarify, file, memory, skills, todo, vision, web | `openrouter/free` | same |
| `document` | Bob | File / Documents | clarify, file, memory, skills, terminal, todo, web | `openrouter/free` | same |
| `comm` | Grace | Communication | clarify, file, memory, skills, todo, web | `openrouter/free` | same |
| `sysmon` | Heidi | System Monitor | clarify, file, memory, skills, terminal, todo, web | `openrouter/free` | same |
| `career` | Frank | Career | clarify, file, memory, skills, todo, web | `openrouter/free` | same |

> `lms` is an **UI-only** agent. There is no `lms` Hermes profile — see §6.

`hermes profile describe <id>` returns the one-line description the **kanban
orchestrator** uses to decide who gets a card:

```
$ hermes profile describe research
Finds, reads and summarizes information from the web, papers and videos. Cites sources.
```

---

## 2. How the CEO delegates — the Kanban board

`~/.hermes/kanban.db` is a **SQLite board shared by every profile**. It is the only
coordination mechanism; there is no message bus between agents.

### Tables (real schema, abridged)

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,             -- 't_7944ce74'
    title TEXT NOT NULL,
    body TEXT,                      -- the actual instruction
    assignee TEXT,                  -- profile id: 'research', 'pc', 'default'…
    status TEXT NOT NULL,           -- ready|running|blocked|done|failed|archived
    priority INTEGER DEFAULT 0,
    created_by TEXT, created_at INTEGER,
    started_at INTEGER, completed_at INTEGER,
    workspace_kind TEXT, workspace_path TEXT,
    claim_lock TEXT, claim_expires INTEGER,   -- atomic claim
    worker_pid INTEGER, worker_started_at INTEGER,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    last_failure_error TEXT, last_heartbeat_at INTEGER,
    current_run_id INTEGER,
    model_override TEXT, provider_override TEXT,
    reasoning_effort TEXT, skills TEXT, max_retries INTEGER,
    goal_mode INTEGER NOT NULL DEFAULT 0,        -- Ralph-style goal loop
    block_kind TEXT, block_recurrences INTEGER NOT NULL DEFAULT 0,
    result TEXT, completion_contract TEXT
);

CREATE TABLE task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL, run_id INTEGER,
    kind TEXT NOT NULL,             -- created|claimed|spawned|heartbeat|commented|
                                    -- completed|blocked|failed|crashed|gave_up|
                                    -- promoted|reclaimed
    payload TEXT, created_at INTEGER
);

CREATE TABLE task_comments (id, task_id, author, body, created_at);
CREATE TABLE task_runs    (id, task_id, profile, step_key, status, claim_lock,
                           claim_expires, worker_pid, worker_started_at,
                           max_runtime_seconds, last_heartbeat_at, started_at,
                           ended_at, outcome, summary, metadata, error);
CREATE TABLE task_attachments (id, task_id, filename, stored_path, content_type, size, uploaded_by, created_at);
CREATE TABLE task_links    (parent_id, child_id);   -- dependencies
CREATE TABLE kanban_notify_subs (task_id, platform, chat_id, thread_id, …);
```

### The full delegation cycle

```
1. human says "research forex trading and make a PDF"
2. CEO (default profile) creates a card:
     hermes kanban create "Research: forex trading" \
       --body-file - --assignee default --workspace scratch
   → t_7944ce74, status=ready, assignee=default
3. the gateway's dispatcher claims it atomically
   (claim_lock + claim_expires), spawns a worker process
   → events: claimed, spawned
4. worker runs, heartbeats, writes tool calls into its own state.db,
   writes progress as task_events
5. CEO decides "this needs the research agent" and creates a CHILD card:
     hermes kanban create "Research: forex" --assignee research …
   → and links them: hermes kanban link <parent> <child>
6. research claims it, works in ITS OWN workspace dir
   (kanban/workspaces/t_xxxx/), writes the result into tasks.result
7. CEO reads the child's result, produces the PDF, and completes the parent
   → event: completed, payload {"summary": "…"}
8. a human/bridge reads the card back and speaks the answer
```

### The commands that matter

```bash
hermes kanban create <title> --body-file - --assignee <profile> --workspace scratch
hermes kanban list                      # tasks
hermes kanban show <task-id>             # card + comments + events
hermes kanban assign <task-id> <profile>
hermes kanban claim <task-id>            # atomic claim, prints workspace path
hermes kanban complete <task-id> --summary "…"
hermes kanban block <task-id> --reason "…"
hermes kanban link <parent> <child>     # dependency
hermes kanban dispatch / daemon / watch # manual dispatch / resident dispatcher
hermes kanban decompose <task-id>        # split into a graph
hermes kanban swarm <…>                 # parallel workers → verifier → synthesizer
hermes kanban stats / diagnostics / repair / gc
```

---

## 3. Honcho — cross-session user modelling

**Honcho is a Hermes *plugin* (memory provider), not a skill and not a separate service
you wire up by hand.** Two halves ship with Hermes:

| Path | What |
|---|---|
| `~/.hermes/hermes-agent/plugins/memory/honcho/` | The provider: `client.py`, `dialectic.py`, `session.py`, `oauth.py`, `peer` tools, `plugin.yaml` |
| `~/.hermes/hermes-agent/optional-skills/autonomous-ai-agents/honcho/SKILL.md` | The operator guide (setup, cloud vs self-hosted, peers, troubleshooting) |

### Setup

```bash
hermes memory setup honcho        # cloud (OAuth / device code / API key) or self-hosted
hermes honcho status               # resolved config, connection test, peer info
```

The `honcho-ai` SDK is prepared by the setup wizard into the selected environment —
**do not `pip install` it into the profile venv yourself**; the wizard owns that.

### How it changes an assistant

Honcho models a conversation as interactions between two **peers**:

- a **user peer** — the human; Honcho builds a *representation* (preferences, facts, patterns)
- an **AI peer** — *one per Hermes profile*, so each assistant develops an independent
  view while sharing one picture of the user.

On each turn the base context injected into the system prompt is assembled in this
order:

1. **Session summary** — a digest of the current session, so the model has continuity
   without replaying the whole history
2. **User representation** — the accumulated model of the human
3. **AI peer card** — the identity card for *this* profile's peer

Cold start (no prior session / empty representation) → lightweight intro prompt, no
summary injection, "encourage the model to learn about the user".
Warm start → full base-context injection, richer prompt.

This is automatic; nothing to configure per profile.

### Honcho vs the local memory files

| | Local `memories/MEMORY.md` | Honcho |
|---|---|---|
| Storage | a markdown file per profile | Honcho's own service (cloud or self-hosted) |
| Format | `§`-separated blocks | internal representations + peers |
| Read by | `memory` tool | injected into the system prompt automatically |
| Good for | durable facts, pinned rules | who the user is, evolving preferences, cross-session continuity |

They coexist. The local files are the floor; Honcho is the model.

---

## 4. Skills

A skill is a **directory with a `SKILL.md`** (YAML front-matter + markdown body).
Skills are *documentation-plus-procedure*, not code — the model reads them on demand.

```
~/.hermes/skills/
  research/  productivity/  software-development/  devops/  education/  …
  <category>/<skill-name>/SKILL.md
```

Real skill front-matter:

```yaml
---
name: honcho
description: Configure and troubleshoot Honcho memory for Hermes.
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Honcho, Memory, Profiles, Observation, Dialectic, User-Modeling, Session-Summary]
prerequisites:
  pip: [honcho-ai]
---
```

Every profile sees the same library. A skill becomes available to a profile when:

1. it is in the shared `~/.hermes/skills/` tree, **and**
2. the profile's `platform_toolsets.cli` includes `skills` (otherwise the agent cannot
   even read the catalogue), **and**
3. it is named in `--skills <name>` on the dispatch, or auto-selected by the model.

`hermes skills` manages the library; the `skill` tool is what the agent calls.

---

## 5. Memory

Three distinct stores, all real:

| Store | Where | Written by | Read by |
|---|---|---|---|
| Personal notes | `~/.hermes/memories/MEMORY.md` (`§`-separated) | `memory` tool | `memory` tool; also injected as a nudge every `nudge_interval` turns (10) |
| User profile | `~/.hermes/memories/USER.md` | `memory` tool | same, with `user_char_limit` 1375 vs `memory_char_limit` 2200 |
| Session history | `state.db` `messages` table | the agent | `--resume`, `session_search` tool, `context` |

Real content from `USER.md`:

```
User works with Class 5 ABS Science material (chapter "The Human Body")…
§
User writes in Roman Urdu mixed with English and expects replies in simple Roman English…
§
User's WhatsApp voice notes usually fail — transcription or download errors — so his
spoken messages often arrive as garbled text. Ask him to retype rather than guessing intent.
```

`MEMORY.md` also carries **operational rules** that the agent follows as if they were
its own — e.g. *"Env quirks: Vision tool cannot analyze images — no LLM provider
configured; always ask user to describe images in text"*, *"Must verify before
reporting — sub-agent summaries are claims, not evidence"*, *"Delivery: put paths in
MEDIA: tag"*.

---

## 6. LMS — the one integration that is NOT a Hermes profile

The NUML Moodle integration is a **standalone Python client** in the Helix repo, not
an agent:

```
helix/tools/lms_client.py     # the Moodle client
  BASE_URL = "https://lms2.numl.edu.pk/"
  CONFIG   = ~/.config/helix/lms.env     # LMS_USERNAME / LMS_PASSWORD (chmod 600)
  class LMSClient:
      login()                  # GET login/index.php → logintoken → POST username/password
      dashboard()              # my/ → [{id, name, url}]
      course(id)               # course/view.php → modules[], assignments[], attendance[]
      assignment(id)           # mod/assign/view.php → submitted?, due, grading_status
      attendance(id)           # mod/attendance/view.php → points, percentage, sessions[]
      download(url)            # → ~/Downloads/helix-lms/<name>
      upload_assignment_draft(assignment_id, file_path)   # NEVER submits for grading
```

The bridge exposes it to the UI:

| Bridge route | LMS call |
|---|---|
| `GET /lms/state` | `state()` → dashboard |
| `GET /lms/course?id=` | `client().course(id)` |
| `GET /lms/assignments` | dashboard + every course's assignments |
| `GET /lms/attendance?course_id=` | attendance per course |
| `POST /lms/download` | `client().download(url)` |
| `POST /lms/upload` | `client().upload_assignment_draft()` — requires `confirm=1` **and** a real file; uploads a *draft*, never submits |

**Critical rule that must survive a renovation:** the upload path writes a *draft*.
Submitting for grading is a separate, deliberate act.

---

## 7. The data layer — which DB holds what

| DB | Path | Holds | Read by |
|---|---|---|---|
| **Kanban board** | `~/.hermes/kanban.db` | tasks, events, comments, runs, attachments, links | the bridge, the UI, `hermes kanban` |
| **Per-profile state** | `~/.hermes/profiles/<id>/state.db` | that profile's sessions, messages, tool calls, `gateway_routing` (token usage) | the agent, `session_search`, `activity` |
| **Default state** | `~/.hermes/state.db` | the CEO's version of the same | same |
| **Eras store** | `~/.hermes/eras.db` (15 MB) | long-term semantic store | `eras.py` |
| **Cron** | `~/.hermes/cron/executions.db`, `deliveries.db`, `notepad.db` | job runs, deliveries, notes | the cron ticker |
| **Documents cache** | `~/.hermes/cache/documents/` | files the agent has seen (PDFs, images) | agents via `file`/cache tools |

**Why it matters for a renovation:** the UI reads the **board** for agents/tasks and
**every profile's `state.db`** for tool activity. A single-profile Jarvis has one
`state.db` and no board — so it has no "team" to show and no way to render "the
research agent is working on X".

---

## 8. The gateway — the always-on process

```bash
hermes gateway run       # long-running; PID + state in ~/.hermes/gateway.pid / gateway_state.json
hermes gateway status
```

Real `gateway_state.json`:

```json
{ "pid": 700559, "kind": "hermes-gateway", "argv": ["…/hermes_cli/main.py","gateway","run"],
  "gateway_state": "running", "active_agents": 0,
  "platforms": { "whatsapp": { "state": "connected", "writer_pid": 700559, … } } }
```

The gateway does three jobs:

1. **Dispatches Kanban cards** to idle profiles (`kanban.dispatch_in_gateway: true`,
   `dispatch_interval_seconds: 5`, `max_in_progress: 3`). This is what makes the
   team work while nobody is watching.
2. **Owns the messaging channels** (whatsapp/telegram/discord/slack/signal/… each
   bound to a `hermes-<platform>` toolset). The gateway is the only thing that
   talks to WhatsApp.
3. **Guards itself**: `loop_watchdog`, `startup_watchdog`, `bot_loop_guard`,
   `restart_loop_guard`, `respawn_storm` — each with limits, so a crashing profile
   cannot take the whole system down.

`~/.hermes/gateway.sock` is the Unix socket the gateway listens on.

---

## 9. Cron — the scheduled assistant

`~/.hermes/cron/jobs.json` holds the jobs; `executions.db` holds the runs. Two real
jobs on this box:

| id | script | what |
|---|---|---|
| `b30aa3f81674` | `helix-watchdog.sh` | health/heartbeat |
| `9284054cf53e` | prompt: "You are sending HELIX's daily briefing to the human over WhatsApp…" | the daily briefing |

`hermes cron` manages these; `deliveries.db` records what was actually delivered to
which channel.

---

## 10. How HELIX wires all of this into one screen

`bridge/bridge_ws.py` is the only new code. It is a **stdlib-only WebSocket server**
on a random free loopback port, and it does four things:

### 1. Reads the board → emits UI events

```
board row                         →  event
──────────────────────────────────────────────────────────
tasks[]                           →  task.upsert  {id,title,assignee,status,summary}
profiles[] (status + current run) →  agent.status  {agent,status,task,progress}
task_events[]                     →  tool.call    {agent,tool,input,output,ok}
a task reaching status=done       →  chat         {role:'agent', agent, text:summary}
```

The id mapping matters: Hermes calls the CEO `default` and the document agent
`document`; the UI calls them `helix` and `files`. `ui_agent()` does that translation.
Without it the chat shows the sender as **"undefined"**.

### 2. Serves the UI over the same origin

The WebView loads `http://127.0.0.1:<port>/?demo=0&bridge=ws://127.0.0.1:<port>`.
Same origin ⇒ the WebSocket is same-origin ⇒ it works. (A `file://` page has an
opaque origin and WebKit will not complete the `ws://` connection.)

### 3. Adds the things Hermes has no HTTP surface for

| Route | Backed by |
|---|---|
| `POST /stt` | `whisper-cli` (ggml-base) — local, no audio leaves the machine |
| `POST /tts` | edge-tts → piper → espeak-ng chain |
| `GET /headlines` | BBC / NPR / Ars Technica / Hacker News RSS |
| `GET /lms/*` | `lms_client.py` |
| `GET /cortex` | counts of memories, skills, SOUL.md files, config.yaml files |
| `GET /activity` | tool calls across **every** profile's `state.db` |

### 4. Broadcasts to every connected client

A background thread polls the board every 1.5 s and queues frames for the event
loop. This is what makes Agent Town actors actually walk to their desks, and what
delivers an agent's finished answer to the chat.

---

## 11. Renovating JARVIS — the checklist

Do these in order; each step is independently verifiable.

### Phase 1 — give Jarvis a team (Hermes profiles)

```bash
hermes profile create research --clone
hermes profile create dev --clone
hermes profile create pc --clone
hermes profile create vision --clone
hermes profile create document --clone
hermes profile create comm --clone
hermes profile create sysmon --clone
hermes profile create career --clone
```

For each: write `SOUL.md` (one paragraph, the persona), set
`platform_toolsets.cli` (the capability boundary), and set `approvals.deny` for
anything destructive. `hermes profile describe <id>` — one line, used by the
orchestrator to route work.

### Phase 2 — give the team a board

```bash
hermes kanban init
hermes gateway run &          # the dispatcher lives here
```

Without the gateway nothing dispatches. With it, cards get claimed and worked
automatically, and Agent Town has something to animate.

### Phase 3 — memory

Local first, Honcho second.

```bash
# local
~/.hermes/memories/MEMORY.md      # durable facts
~/.hermes/memories/USER.md        # who the human is
# honcho
hermes memory setup honcho
hermes honcho status
```

### Phase 4 — skills

Copy skill directories into `~/.hermes/skills/<category>/<name>/SKILL.md`. A skill is
documentation, not code. Keep `skills` in the toolset of every profile that should
have them.

### Phase 5 — the wire

Build one WebSocket bridge that (a) reads the board, (b) translates ids, (c) pushes
`agent.status` / `task.upsert` / `chat`, (d) serves the UI on the same origin.

### Phase 6 — the desktop shell

GTK3 + WebKit2GTK 4.1 (that is what the WebKit2 4.1 typelib on this box is built
against). Load the UI from the bridge's own HTTP origin, not `file://`. Start and
stop the bridge as a child process; give each profile its own AI peer; grant
microphone permission in the app, because WebKit shows no per-site prompt.

### Phase 7 — external integrations

LMS is the pattern: a **plain Python client** + a thin bridge route + credentials in
`~/.config/<app>/*.env` (chmod 600). Never a hardcoded key, never inside the bundle.
Keep the "draft, never submit" rule.

---

## 12. Things that will bite you

| Trap | What actually happened |
|---|---|
| `asyncio.get_event_loop()` in a worker thread | raises on Python 3.14 → the send silently never happened. Capture the loop on its own thread. |
| Reading `state.db` for only the default profile | Measured on this box: 501 tool rows in the default db vs **1071 across all nine** — reading only the default silently drops **53% of real activity**. `document` alone has 371. Read every profile. |
| Treating a Kanban `status` as a live agent state | `running` + `blocked` are per-profile derived states; derive from the board, never from a flag. |
| Assuming a created card gets answered | the creator must **read the card back**; nothing pushes it for you. |
| `file://` for a WebSocket page | opaque origin → WebKit refuses the `ws://` connection. Serve over http and use the same origin. |
| `SpeechRecognition` for dictation | Chrome-only. WebKit2GTK has no such API — record with MediaRecorder and transcribe on the backend. |
| Trusting browser TTS | WebKit2GTK ships no speech-dispatcher voices → silence. Use a server-side chain. |
| Starting the demo/backend before the live one | you get a window full of fake data. Gate on a hard switch. |
| Letting a child process outlive the app | orphan holding a port. `PR_SET_PDEATHSIG` **and** a `getppid()` poll. |
| Assuming a screenshot tool exists | Wayland refuses `gnome-screenshot` and `grim`. Use WebKit's own `get_snapshot()`. |

---

## 13. File map — where everything lives

```
~/.hermes/
├── config.yaml                  CEO's config (model, tools, approvals, gateway)
├── SOUL.md                      CEO persona
├── memories/{MEMORY,USER}.md
├── state.db                     CEO's sessions/messages/tool-calls
├── kanban.db                    ← the shared board
├── eras.db                      long-term semantic store
├── gateway.sock / .pid / gateway_state.json
├── channel_directory.json       which platforms are bound
├── cron/{jobs.json,executions.db,deliveries.db}
├── cache/documents/             files the agents have seen
├── skills/<category>/<skill>/SKILL.md
├── hermes-agent/                the source: plugins/, optional-skills/, tests/
└── profiles/<id>/
    ├── SOUL.md  config.yaml  profile.yaml
    ├── memories/  state.db
    ├── skills/  workspace/  cron/  plugins/  hooks/  platforms/

~/helix/
├── ui/
│   ├── src/{index.html,style.css,js/*.js}     ← edit these
│   ├── build.js → helix-ui.html                ← node build.js
│   └── helix-ui.html                           ← built; served by bridge_ws.py
├── bridge/
│   ├── bridge_ws.py          ← the WebSocket bridge (stdlib only)
│   ├── helix_desktop.py      ← the GTK3 desktop shell
│   └── helix.desktop         ← the .desktop entry
├── tools/
│   ├── lms_client.py         ← the Moodle client (the LMS integration)
│   ├── live_tts.py  eras.py  selfcheck.py
└── docs/
    ├── PACKAGING_PLAN.md     ← desktop app plan + verification
    └── PROGRESS.md           ← the running log
```

---

## 14. One-paragraph summary

An assistant in this system is a **Hermes profile**: a directory with a persona
(`SOUL.md`), a tool allowlist (`platform_toolsets.cli`), a model + fallback chain, a
deny-list for destructive commands, a private `state.db` and a private
`memories/` folder. Nine of them plus `default` (the CEO) form a team that
coordinates through one shared SQLite board, `~/.hermes/kanban.db` — the CEO writes
cards, a named profile claims one atomically, works in its own workspace, and
writes the answer back. **Honcho** is a Hermes *plugin* that gives every profile its
own AI peer and injects a cross-session model of the user into the prompt. **Skills**
are markdown procedures on demand. **LMS** is not an agent at all but a plain Python
client behind a bridge route, writing drafts and never submitting. The **desktop
app** is GTK3 + WebKit2GTK showing a WebSocket bridge that reads the board and
turns it into events the UI can animate — agent status becomes a walking pixel
person, a finished card becomes a chat message, and the bridge adds the endpoints
Hermes has no HTTP surface for (STT, TTS, RSS headlines, LMS).
