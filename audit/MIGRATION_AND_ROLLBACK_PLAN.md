# Migration and Rollback Plan

Nothing in this work is irreversible. Every removal is a move into `backup/` and every
source change is a local commit on a branch.

---

## 1. Git state you can return to

| Repo | Ref | Meaning |
|---|---|---|
| JARVIS | `cffa32d` | `master` as it was before this audit |
| JARVIS | `fe1f911` | snapshot of the owner's uncommitted work, **before** any removal |
| JARVIS | `6ba652b` | Brahma + smart-home removed, `core/` added, policy gate in executor |
| JARVIS | `d93c702` | + `JARVIS/tools` duplicates removed (current HEAD) |
| helix | `e8a64cf` | `main` before this audit |
| helix | `c68326b` | snapshot of pending HELIX work before changes |
| helix | `99c7a38` | shared voice contract + repo hygiene (amended) |
| helix | `3d5929f` | live diagnostic model id (current HEAD) |

Branch for all of it: `audit/consolidation-2026-11-06` in both repos. `master`/`main` are
untouched. **No commit was pushed.**

## 2. Rollback recipes

### Undo everything in JARVIS
```bash
cd AI_WORKSPACE/JARVIS
git checkout master            # back to cffa32d
```
The owner's uncommitted work from before the audit is preserved at `fe1f911`; recover it
with `git checkout fe1f911 -- .` if it was not otherwise saved.

### Undo everything in HELIX
```bash
cd AI_WORKSPACE/helix
git checkout main              # back to e8a64cf
```
Pending work snapshot: `c68326b`.

### Undo only the Brahma / smart-home removal
```bash
cd AI_WORKSPACE/JARVIS
git revert --no-commit 6ba652b && git commit
# or restore the modules from the recovery store:
cp -r ../backup/removed-20261106/brahma_connect .
cp -r ../backup/removed-20261106/smart_home .
cp ../backup/removed-20261106/actions-brahma_connect.py actions/brahma_connect.py
```
Reverting the commit restores the code, the declarations, both dispatch chains, the voice
router and the startup wiring together — which is why it was done as one commit.

### Restore the duplicate trees
```bash
cd AI_WORKSPACE
mv backup/JARVIS-nested-duplicate-20261106 JARVIS/JARVIS
mv backup/HERMES-workspace-duplicate-20261106 HERMES
```
Both are plain directories with intact `.git` inside; the moves were `mv` on the same
filesystem, so nothing was transcoded or re-packed.

### Undo the HELIX voice consolidation
```bash
cd AI_WORKSPACE/helix
git revert 99c7a38 3d5929f
```
The three transports still exist afterwards; reverting only puts their local config back.

### Restore smart-home data
```bash
cp AI_WORKSPACE/backup/removed-20261106/smart_home.sqlite3 AI_WORKSPACE/JARVIS/config/
cp AI_WORKSPACE/backup/removed-20261106/smart_home.key        AI_WORKSPACE/JARVIS/config/
```
The database was never opened, migrated or written by this audit.

## 3. Data safety

| Data | Touched? | Backup |
|---|---|---|
| `memory/personal_memory.sqlite3` | No (never opened for write) | tracked in git, unchanged |
| `memory/*.json`, `*.md` | No | git |
| `chat_history/` | No | untracked, in place |
| `config/api_keys.json` | **No** — never read | in place |
| `~/.hermes/.env` | Read only by `read_gemini_key`, never copied or printed | in place |
| `config/smart_home.sqlite3`, `smart_home.key` | Moved | `backup/removed-20261106/` |
| Brahma device records | Moved | `backup/removed-20261106/config-brahma_connect/` |
| `helix/inbox/` documents | Untracked from git, **files untouched on disk** | in place |

## 4. Behavioural changes to be aware of

| Change | Effect | Reversible how |
|---|---|---|
| Smart-home commands no longer short-circuit | "turn off the fan" now goes to the model like any other request | `git revert 6ba652b` |
| Brahma connect commands no longer short-circuit | device phrases are no longer intercepted | same |
| `file_controller` share lost `device` | `share --device X` returns "Unknown share method" | restore the branch |
| `file_controller` delete/chmod now `consequential` | **the agent path will refuse them without a confirmation token** | edit `core/capabilities.py` |
| `send_message`, `cmd_control`, `computer_control`, `shutdown_jarvis` now `consequential` | same — refused on the agent path without a token | same |
| HELIX voice model id | now JARVIS's `gemini-3.1-flash-live-preview` instead of `gemini-3.8-live` | `HELIX_LIVE_MODEL` env, or revert |
| `helix-live.service` | still runs **`~/helix/tools/live_server.py`**, not this tree — behaviour unchanged until that copy is updated | see §5 |

The `consequential` reclassification is the one change that can surprise a user: an agent
task that used to send a message now stops with `Blocked by policy: …`. That is the intended
safety property, and it is reversible in one line.

## 5. Deployment note (outside the workspace)

```
helix-live.service  ExecStart=.../python /home/abubakargcx/helix/tools/live_server.py
helix-globe.service WorkingDirectory=/home/abubakargcx/gods-eye-view
oci-a1-launch.service ExecStart=... %h/helix/tools/oci-a1-launch.sh
```

The running voice service reads `~/helix`, not `AI_WORKSPACE/helix`. Whether that directory
is the same tree (symlink/bind-mount) or a second copy was checked by inode this session.
**Before expecting the shared-contract change to take effect**, either:

1. point the unit at `AI_WORKSPACE/helix/tools/live_server.py`, or
2. apply the same three-file change to `~/helix/tools/`, or
3. make `~/helix` a symlink to the workspace tree.

Until one of those is done, the workspace change is correct but not live. No service file
was edited and no service was restarted during this audit.

## 6. Recovery-store hygiene

`backup/removed-20261106/` contains `smart_home.key` and Brahma paired-device records.
Treat it as **sensitive**, not as ordinary junk. Once the owner is satisfied the removals
are correct, either encrypt it or delete it; until then it is the rollback path.
