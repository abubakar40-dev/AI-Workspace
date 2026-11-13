# System-Wide Consolidation Report — JARVIS / HELIX / HERMES

**Date:** 2026-11-06
**Machine:** Dell Latitude 5480 — `Wick`
**OS:** Ubuntu 26.04.1 LTS (resolute), kernel 7.0.0-42-generic, GNOME, **Wayland**
**Canonical workspace:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`

> Verification rule used throughout: a component is only marked VERIFIED after the
> running process was observed using the new path **and** it answered a real request.
> Nothing is marked working because a command exited 0.

---

## A. Initial system inventory

| Item | Measured value |
|---|---|
| Root filesystem | `/dev/sda2`, **ext4**, 135 G, **115 G used, 14 G free (90 %)** |
| My Drive | `/dev/sda4`, **NTFS (ntfs3 driver)**, 100 G, 48 G used, 53 G free |
| Mount options | `rw,nosuid,nodev,relatime,uid=1000,gid=1000,acl,iocharset=utf8,prealloc` |
| Home | on the root filesystem (no separate partition), 65 G |
| RAM | 6.9 GiB total, 3.9 GiB used at audit start |
| Swap | `/swap.img`, 4 GiB, 2.4 GiB used at audit start |
| Inodes (root) | 23 % used — not a constraint |
| Session | Wayland |

### NTFS capability test (performed, not assumed)

| Capability | Result |
|---|---|
| Write | OK |
| Symbolic links | **OK** (ntfs3 honours them) |
| Executable bit + run | OK |
| chmod 700 | honoured (`700`) |
| SQLite WAL + integrity_check | OK |
| Python execution | OK |

**Conclusion:** My Drive is safe for source trees, git repos and SQLite. A venv *can*
run there, but venvs are still kept on ext4 because they bind to an interpreter path.

### Running services at start

| Unit | State | ExecStart (before) |
|---|---|---|
| `helix-live.service` | active/enabled | `~/.local/share/helix-live-venv/bin/python /home/abubakargcx/helix/tools/live_server.py` |
| `helix-globe.service` | active/enabled | `npm run dev` with `WorkingDirectory=/home/abubakargcx/gods-eye-view` |
| `hermes-gateway.service` | active/enabled | `~/.hermes/hermes-agent/.hermes/bin/hermes gateway run` |
| `oci-a1-launch.service` | active/enabled | `bash %h/helix/tools/oci-a1-launch.sh` |
| `jarvis-claude-gateway.service` | inactive/disabled | `~/JARVIS/scripts/start-claude-gateway.sh` (**path did not exist**) |

---

## B. Complete path inventory

| Component | Original / active path | Now | Status |
|---|---|---|---|
| JARVIS source (canonical) | `AI_WORKSPACE/JARVIS` | unchanged, `audit/consolidation-2026-11-06` @ `d93c702` | VERIFIED PRESENT |
| JARVIS source (old repo) | `My Drive/JARVIS` (master@cffa32d, **134 dirty**) | `AI_WORKSPACE/backup/JARVIS-old-repo-20261106` | PRESERVED, superseded |
| JARVIS source (nested dup) | `AI_WORKSPACE/backup/JARVIS-nested-duplicate-20261106` | unchanged | 1.5 G, removable |
| JARVIS source (home) | `~/JARVIS.bak` | unchanged | 1.9 G, removable |
| JARVIS memory DB | `AI_WORKSPACE/JARVIS/memory/personal_memory.sqlite3` | unchanged (57,344 B, mtime Oct 28) | identical to old copy |
| JARVIS chat history | `AI_WORKSPACE/JARVIS/chat_history/` | **2 missing files copied in** (23 files now) | data preserved |
| JARVIS config/secrets | `AI_WORKSPACE/JARVIS/config/api_keys.json` | untouched | not read |
| HELIX source (canonical) | `AI_WORKSPACE/helix` | unchanged @ `99c7a38` | VERIFIED RUNNING |
| HELIX source (previous live) | `My Drive/hermes/helix` (main@e8a64cf, 42 dirty) | still on disk, service no longer uses it | rollback |
| `~/helix` | symlink → `My Drive/hermes/helix` | unchanged, now unused | rollback |
| `~/helix.bak` | `~/helix.bak` | unchanged | 83 M, removable |
| HELIX venv | `~/.local/share/helix-live-venv` | unchanged (ext4) | required |
| HELIX STT models | `~/.local/share/helix-stt` | unchanged | used by Hermes STT command |
| Hermes runtime (live) | `~/.hermes` (6.6 G) | unchanged | VERIFIED RUNNING |
| Hermes (stale copy) | `AI_WORKSPACE/.hermes` (7.4 G) | unchanged | stale, superseded |
| Hermes (workspace dup) | `AI_WORKSPACE/backup/HERMES-workspace-duplicate-20261106` (6.3 G) | unchanged | removable |
| Hermes home | `My Drive/hermes` (851 M: cache/helix/plugins/skills) | unchanged | needs inspect before removal |
| God's Eye View (live svc) | `~/gods-eye-view` (499 M) | **no longer used**; service runs workspace copy | removable |
| God's Eye View (canonical) | `AI_WORKSPACE/gods-eye-view` | unchanged, `main@0dbde1e` | VERIFIED SERVING |
| Desktop | `~/Desktop` **real dir, 4.2 G on ext4** | **symlink → `My Drive/Desktop`** | VERIFIED |
| Downloads | `~/Downloads` symlink + XDG → `My Drive/Downloads` | unchanged | VERIFIED |
| Old downloads | `My Drive/Download` (289 M, 28 unique files) | `AI_WORKSPACE/backup/Download-old-20261106` | PRESERVED |
| Ollama | installed, server not running, models dir 40 K | unchanged | nothing to clean |
| Docker | 5 containers / 7 images, 11.36 G | unchanged | 6.4 G reclaimable |
| PostgreSQL | inside 2 Docker containers (Dental Lounge) | unchanged | **unrelated to JARVIS/HELIX/Hermes** |

---

## C. Downloads / Desktop recovery

**Diagnosis.** XDG was already correct (`user-dirs.dirs` → My Drive), but `~/Desktop`
was a **real directory containing a second copy** of the desktop, while GNOME was showing
`My Drive/Desktop`. That is exactly the "duplicate folders" symptom described.

**What was done.**

1. File-level comparison of both trees (180,615 files in home vs 180,752 on My Drive).
2. Home-only files: **30** → copied into `My Drive/Desktop` (additive, no overwrites).
3. Re-scan: **0 files remain only in home** → My Drive is a verified superset.
4. `~/Desktop` renamed to `~/Desktop.old-20261106` (not deleted), then symlinked to
   `My Drive/Desktop`.
5. `My Drive/Download` (the singular old folder, 28 unique files) moved to
   `AI_WORKSPACE/backup/Download-old-20261106`.

**Verification.**

```
~/Desktop   -> /run/media/abubakargcx/My Drive/Desktop   [resolves to /dev/sda4 ntfs3]
write test on ~/Desktop/.write-test-<pid> : OK, physically on sda4
xdg-user-dir DESKTOP   -> /run/media/abubakargcx/My Drive/Desktop
xdg-user-dir DOWNLOAD  -> /run/media/abubakargcx/My Drive/Downloads
```

Application-specific download paths were **not** all audited (Chrome/Firefox/Telegram
each keep their own setting). Chrome and Firefox store to their own configured folder if
set; this was not changed because it was not verified.

---

## D. JARVIS migration

| Item | Result |
|---|---|
| Canonical repo | `AI_WORKSPACE/JARVIS`, branch `audit/consolidation-2026-11-06`, HEAD `d93c702`, 236 tracked, worktree clean |
| Old repo | 134 dirty entries; **every dirty file verified** against the canonical copy: 68 identical, 14 differ (they are exactly the files the earlier consolidation edited), 5 absent (removed on purpose) |
| Unique data found in old copy | `chat_history/2026-11-04.md`, `2026-11-05.md` → **copied to canonical** |
| Memory DB | byte-identical in both (57,344 B, same mtime); no `-wal` content (0-byte WAL, transient `-shm`) |
| Runtime | no JARVIS process/service is running; it is started manually |
| `jarvis-claude-gateway.service` | disabled; its `ExecStart` pointed at `~/JARVIS/scripts/...` which did not exist. The script exists under the canonical tree — **unit not repointed** (see outstanding) |

**Verdict: MIGRATED, NOT YET RUNTIME VERIFIED.** JARVIS was not launched, because
launching it would open a live voice session and requires the user present.

---

## E. HELIX migration

**Previous deployment:** `~/helix` → `My Drive/hermes/helix` (main@e8a64cf, 42 dirty).
**Canonical development copy:** `AI_WORKSPACE/helix` @ `99c7a38`, worktree clean.

Comparison proved the canonical copy is a **superset**: every dirty path in the live tree
exists in the canonical tree; 17 identical, 3 differ (`.gitignore` gains ignore rules,
`ui/node_modules` and `ui/src` — present in both).

**Service changes** (units backed up to `AI_WORKSPACE/backup/systemd-units-20261106/`):

| Unit | Change |
|---|---|
| `helix-live.service` | ExecStart → `AI_WORKSPACE/helix/tools/live_server.py`; added `Environment="JARVIS_ROOT=AI_WORKSPACE/JARVIS"`; removed now-inert `HELIX_LIVE_MODEL` / `HELIX_LIVE_VOICE` |
| `helix-globe.service` | `WorkingDirectory` → `AI_WORKSPACE/gods-eye-view` |
| `oci-a1-launch.service` | `ExecStart` → `AI_WORKSPACE/helix/tools/oci-a1-launch.sh` |

**Two real failures hit and fixed during the switch** (recorded because they are the
exact class of bug that makes a migration look successful):

1. `ExecStart` was unquoted → systemd split `/run/media/.../My Drive/...` at the space and
   the process failed with `can't open file '/run/media/abubakargcx/My'`.
2. `Environment=JARVIS_ROOT=...` was also unquoted → the value truncated to
   `/run/media/abubakargcx/My`, so the voice proxy refused to start with
   `HELIX requires the shared JARVIS voice core ...`.

Both fixed by quoting. `NRestarts=0`, no restart loop.

**Verification (real, not structural):**

```
helix-live    active      helix-globe  active
helix         LISTEN 127.0.0.1:8788
handshake     HTTP/1.1 101 Switching Protocols
proxy ready   {"type":"ready","model":"gemini-3.1-flash-live-preview","voice":"Charon"}
state         connected
reply         "bridge ok"          (real Gemini Live round-trip)
state         listening
globe         HTTP 200 on http://127.0.0.1:4173/
globe process node .../AI_WORKSPACE/gods-eye-view/node_modules/.bin/vite
```

**Behaviour change to note:** HELIX now uses the shared model
`gemini-3.1-flash-live-preview` instead of its old `gemini-3.8-live` override, because the
unit's override was inert once the contract became authoritative. This is the intended
single-source outcome, and it was confirmed working against Gemini.

**Verdict: VERIFIED WORKING** (text turn). Audio in/out not tested — no mic capture was
performed.

---

## F. Hermes migration

| Item | Result |
|---|---|
| Live runtime | `~/.hermes`, 6.6 G, 1,613 files changed since Nov 1 → **authoritative** |
| Gateway | `hermes-gateway.service` active; `HERMES_HOME=/home/abubakargcx/.hermes` |
| Stale copy | `AI_WORKSPACE/.hermes`, 7.4 G, only 1,046 files changed since Nov 1 → older |
| Workspace duplicate | `AI_WORKSPACE/backup/HERMES-workspace-duplicate-20261106`, 6.3 G |
| Additional | `My Drive/hermes` 851 M (`cache`, `helix`, `plugins`, `skills`) — not yet mapped to a consumer |

Hermes was **not reinstalled and not reconfigured**. It remains in home because its own
unit hard-codes `HERMES_HOME=/home/abubakargcx/.hermes` and its updater repairs its
checkout in place; relocating it is a supported-configuration question, not a file move.

**Verdict: RETAINED IN HOME — REQUIRED EXCEPTION.**

---

## G. Infrastructure cleanup

| Component | Finding | Action |
|---|---|---|
| PostgreSQL | 12 processes, all children of **two Docker containers** (`thedentallounge-db-1`, `dental-lounge-ui-v2-db-1`, `postgres:17-alpine`, healthy 4 h) | **Retained** — belongs to the user's Dental Lounge project, not to JARVIS/HELIX/Hermes |
| Docker | 5 containers (2 running, 3 exited ≥3 weeks), 7 images, 11.36 G, **6.387 G reclaimable** | Proposed for approval |
| Ollama | Installed, server not running, `~/.ollama` = 40 K → **no models stored** | Nothing to remove |
| Playwright | `~/.cache/ms-playwright` 1.9 G | Retained (JARVIS browser automation) |
| `oci-a1-launch` | Running the capacity hunter from the canonical tree | Retained |

---

## H. Home-directory leftovers (every JARVIS/HELIX/Hermes-related item)

| Path | Size | Why it is still there |
|---|---|---|
| `~/Desktop.old-20261106` | 4.2 G | Rollback copy after the symlink switch; awaiting approval |
| `~/JARVIS.bak` | 1.9 G | Pre-existing backup; canonical repo supersedes it |
| `~/helix.bak` | 83 M | Pre-existing backup; canonical repo supersedes it |
| `~/helix` (symlink) | — | Rollback pointer to `My Drive/hermes/helix`; no service uses it now |
| `~/gods-eye-view` | 499 M | Previous deploy root; service now uses the workspace copy |
| `~/.hermes` | 6.6 G | **Live Hermes runtime (required exception)** |
| `~/.local/share/helix-live-venv` | — | Interpreter for `helix-live.service` |
| `~/.local/share/helix-stt` | — | STT binary+model used by `HERMES_LOCAL_STT_COMMAND` |
| `~/.local/share/mamba` | — | Unrelated desktop app (running) |
| `~/easy-diffusion.bak` | 4.4 G | Unrelated to these three projects (image tool backup) |
| `~/.vscode.bak`, `~/.config/Code.bak` | 1.2 G + 1.2 G | Editor backups, not project data |
| `~/.opencode.bak`, `~/.cursor.bak` | 230 M + 5.9 M | Editor backups |

Everything else in home is OS/app data and was left alone.

---

## I. Storage comparison (measured)

| Metric | Before | Now | Note |
|---|---|---|---|
| Root used | 115 G / 135 G (90 %) | **115 G (90 %)** | nothing deleted yet — deliverables still held for rollback |
| Root free | 14 G | **14 G** | |
| Home | 65 G | 65 G | `~/Desktop` 4.2 G now counted inside `Desktop.old` |
| My Drive used | 48 G | ~48 G | top-level `JARVIS` renamed into `AI_WORKSPACE/backup`, so `AI_WORKSPACE` grew 25 G → 27 G |
| AI_WORKSPACE | 25 G | 27 G | +2 G is the relocated old repo |
| RAM used | 3.9 GiB | ~4.1 GiB | unchanged by design; no service was removed |

**No RAM claim is made.** No process was stopped to manufacture an improvement.

Measured reclaim potential:
- **Root filesystem ≈ 13.7 G** (Desktop.old 4.2 + easy-diffusion.bak 4.4 + JARVIS.bak 1.9 +
  Code.bak 1.2 + vscode.bak 1.2 + gods-eye-view 0.5 + opencode.bak 0.23 + helix.bak 0.08)
- **My Drive ≈ 20 G** (`.hermes` stale 7.4 + HERMES dup 6.3 + nested JARVIS 1.5 + old repo
  1.9 + tarballs ~2.2 + `hermes` 0.85)
- **Docker ≈ 6.4 G** (unrelated to projects)

---

## J. Outstanding approval items — `GREEN SIGNAL` required

Nothing below has been executed. Each entry is a permanent deletion.

### Root filesystem (frees ≈ 13.7 G)

| # | Exact path | Size | Why safe |
|---|---|---|---|
| 1 | `/home/abubakargcx/Desktop.old-20261106` | 4.2 G | My Drive/Desktop verified superset (0 home-only files) |
| 2 | `/home/abubakargcx/easy-diffusion.bak` | 4.4 G | Unrelated image-tool backup |
| 3 | `/home/abubakargcx/JARVIS.bak` | 1.9 G | Canonical repo verified superset; chat files preserved |
| 4 | `/home/abubakargcx/.config/Code.bak` | 1.2 G | Editor backup |
| 5 | `/home/abubakargcx/.vscode.bak` | 1.2 G | Editor backup |
| 6 | `/home/abubakargcx/gods-eye-view` | 499 M | Globe verified serving from the workspace copy |
| 7 | `/home/abubakargcx/.opencode.bak` | 230 M | Editor backup |
| 8 | `/home/abubakargcx/helix.bak` | 83 M | Canonical repo superset |
| 9 | `/home/abubakargcx/.cursor.bak` | 5.9 M | Editor backup |

### My Drive (frees ≈ 20 G)

| # | Exact path | Size | Why safe |
|---|---|---|---|
| 10 | `AI_WORKSPACE/.hermes` | 7.4 G | Older copy of live `~/.hermes` (fewer recent changes) |
| 11 | `AI_WORKSPACE/backup/HERMES-workspace-duplicate-20261106` | 6.3 G | Duplicate of `~/.hermes` |
| 12 | `AI_WORKSPACE/backup/JARVIS-old-repo-20261106` | 1.9 G | Verified superseded by canonical repo |
| 13 | `AI_WORKSPACE/backup/JARVIS-nested-duplicate-20261106` | 1.5 G | Verified duplicate |
| 14 | `AI_WORKSPACE/backup/*.tar.gz` + `*.gpg` (JARVIS, gods-eye-view, helix, helix-live-venv, helix-stt) | ≈ 2.2 G | Pre-existing tarballs; sources verified present |
| 15 | `My Drive/hermes/helix` (via `~/helix`) | ~0.6 G | No service uses it; canonical HELIX verified running |

### Infrastructure

| # | Item | Size | Note |
|---|---|---|---|
| 16 | 3 exited Docker containers + 5 unused images | 6.4 G | **Unrelated to the three projects** — Dental Lounge containers must stay |

### Deferred / needs a decision, not a GREEN SIGNAL

- `My Drive/hermes` (851 M: `plugins`, `skills`) — must be checked against Hermes skill
  discovery before touching.
- `~/.cache/pip` (1.3 G), `~/.cache/huggingface` (858 M), `~/.cache/tracker3` (1.1 G) —
  recreatable caches, unrelated to project data.
- `.config/omnirush` (5.9 G) + `~/.omnirush` (3.9 G) — a third-party AI gateway, untouched.
- `jarvis-claude-gateway.service` — disabled unit with a dead `ExecStart`; needs repointing
  or removal.

---

## K. Final architecture and path map

```
/run/media/abubakargcx/My Drive/
├── AI_WORKSPACE/                      27 G  ← single canonical workspace
│   ├── JARVIS/                        repo, audit/consolidation-2026-11-06 @ d93c702
│   │   ├── core/  agent/  actions/  agents/  memory/  chat_history/  tests/
│   │   └── venv/ (ext4-bound, kept in place)
│   ├── helix/                         repo, audit/consolidation-2026-11-06 @ 99c7a38
│   │   ├── tools/  bridge/  ui/  docs/  agents/
│   │   └─ imports ../../JARVIS/core/voice.py  (shared voice contract)
│   ├── gods-eye-view/                 repo, main@0dbde1e  ← live globe
│   ├── DATA/  LMS Docs/  audit/
│   └── backup/
│       ├── JARVIS-old-repo-20261106/          (rollback)
│       ├── JARVIS-nested-duplicate-20261106/  (rollback)
│       ├── HERMES-workspace-duplicate-20261106/ (rollback)
│       ├── Download-old-20261106/
│       ├── systemd-units-20261106/
│       └── removed-20261106/                  (Brahma, smart-home, HELIX copies)
├── Desktop/                           ← XDG_DESKTOP_DIR (live)
├── Downloads/                         ← XDG_DOWNLOAD_DIR (live)
└── hermes/                            (plugins, skills — under review)

/home/abubakargcx/
├── Desktop -> /run/media/abubakargcx/My Drive/Desktop      (symlink)
├── Downloads -> /run/media/abubakargcx/My Drive/Downloads  (symlink)
├── .hermes/                           6.6 G  LIVE Hermes runtime (exception)
├── .local/share/helix-live-venv/      interpreter for helix-live
├── .local/share/helix-stt/            STT model for Hermes
└── Desktop.old-20261106, JARVIS.bak, helix.bak, gods-eye-view, *.bak  (await approval)
```

**Service → path map (verified):**

| Unit | Executes | Working dir |
|---|---|---|
| `helix-live` | `AI_WORKSPACE/helix/tools/live_server.py` | — |
| `helix-globe` | `AI_WORKSPACE/gods-eye-view` vite | `AI_WORKSPACE/gods-eye-view` |
| `oci-a1-launch` | `AI_WORKSPACE/helix/tools/oci-a1-launch.sh` | — |
| `hermes-gateway` | `~/.hermes/hermes-agent/.hermes/bin/hermes` | `~/.hermes` |

---

## L. Verification verdict

| Component | Verdict |
|---|---|
| Canonical workspace | **VERIFIED** — one root, four repos, no nested duplicates outside `backup/` |
| Downloads on My Drive | **VERIFIED** — XDG + symlink, write test lands on `sda4` |
| Desktop on My Drive | **VERIFIED** — superset merge, symlink, write test on `sda4` |
| HELIX voice (live) | **VERIFIED WORKING** — WS 101 + Gemini `connected` + real reply |
| HELIX globe | **VERIFIED WORKING** — HTTP 200, process runs from canonical path |
| HELIX duplicate removal | **READY FOR CLEANUP APPROVAL** |
| JARVIS | **MIGRATED, NOT YET RUNTIME VERIFIED** — repo consolidated, data preserved, app not launched |
| Hermes | **VERIFIED RUNNING**; **RETAINED IN HOME — REQUIRED EXCEPTION** |
| Hermes stale copy (7.4 G) | **READY FOR CLEANUP APPROVAL** |
| PostgreSQL | **RETAINED** — belongs to an unrelated project |
| Docker | **READY FOR CLEANUP APPROVAL** (6.4 G, project-unrelated) |
| Ollama | **NOTHING TO CLEAN** — zero models stored |
| Home-directory cleanliness | **PARTIALLY MIGRATED** — all remaining items are listed in §H with a reason |
| Mount-failure safety | **BLOCKED** — not tested; unmounting during DB writes was out of scope |

### Known limitations of this report

1. JARVIS was not started; its runtime paths are inspected, not proven.
2. Audio capture/playback was not tested for either assistant.
3. Browser/Telegram/Chrome download directories were not individually audited.
4. Behaviour when My Drive is unmounted was not tested.
5. `My Drive/hermes` (plugins/skills) is not yet mapped to a consumer.
