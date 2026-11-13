# HELIX Working-Line Decision

**Mode:** read-only. No merge, no restore, no branch movement, no switch of `helix-live.service`. Both trees and the SHA256-verified backup are untouched.

---

## 1. The finding that decides this question

Batches 04–06 framed HELIX as **two competing lines**: a clean active tree and a dirty "preserved WIP/refactor line." Batch 07 tested that framing with git lineage and byte-level comparison, and it does not hold.

**Line A is a descendant of Line B.**

```
e8a64cf  Repair Helix dispatch and gesture runtime      <- /home/abubakargcx/helix HEAD (= main, = origin/main)
   |
   +-- c68326b  Checkpoint: pre-consolidation working state on an audit branch
   |
   +-- 07a2522  Consume the shared JARVIS voice contract instead of carrying a second one
   |
   +-- 99c7a38  Point the live diagnostic at the same model the proxy uses   <- AI_WORKSPACE/helix HEAD
```

Evidence:
- `git -C AI_WORKSPACE/helix cat-file -t e8a64cf` → `commit` (Line A contains Line B's head).
- `git -C /home/abubakargcx/helix cat-file -t 99c7a38` / `c68326b` → `fatal: Not a valid object name` (Line B is behind).
- `git -C AI_WORKSPACE/helix log --oneline e8a64cf..99c7a38` → exactly the three commits above.
- In the Line A repo, `main` and `origin/main` both still point at `e8a64cf`. **The consolidation work exists only on the local audit branch.**

**Line B's "WIP" is the checkpoint commit.** Comparing all 75 Line-B working-tree files (excluding `ui/node_modules`, `__pycache__`, `*.pyc`) against the `c68326b` tree:

| Result | Count | Detail |
|---|---:|---|
| Byte-identical to checkpoint | **69** | includes `bridge/bridge_ws.py`, `ui/build.js`, `ui/src` (all 12 files), `docs/AGENT_ARCHITECTURE.md`, `tools/lms_client.py`, `install.sh` |
| Differs from checkpoint | **5** | `.gitignore`, `tools/check-live.py`, `tools/helix_voice.py`, `tools/live_server.py`, `tools/live_tts.py` |
| Only in Line B | **1** | `logs/oci-a1-launch.log` (a runtime log) |

So the deletions that made Line B look like a radical refactor (`bridge/server.py`, `ui/console/*`, `ui/shell/*`, `ui/voice-core/*`, `ui/world-monitor/*`, `tools/helix_app.py`, `tools/gesture.py`, …) are **already committed** in `c68326b`, and their replacements (`bridge_ws.py`, `ui/src`, desktop launcher, LMS client) are committed too and still present at `99c7a38`.

---

## 2. Line-by-line comparison

| Dimension | Line A — `AI_WORKSPACE/helix` | Line B — `/home/abubakargcx/helix` |
|---|---|---|
| Git state | `99c7a38`, branch `audit/consolidation-2026-11-06`, **clean (0 porcelain)** | `e8a64cf`, branch `main`, **42 porcelain** (22 deletions, 15 untracked, 5 modified) |
| Relationship | Contains Line B's head; 3 commits ahead | Ancestor, with uncommitted working-tree deltas |
| Runtime relationship | `helix-live.service` (user unit, active, enabled) → `tools/live_server.py` on `127.0.0.1:8788` | **Not referenced by any unit**; no mapped process |
| Service relationship | `JARVIS_ROOT` now resolves (`AI_WORKSPACE/JARVIS` exists) | — |
| Spec/architecture docs | `docs/HELIX_BUILD_SPEC.md`, `AGENT_ARCHITECTURE.md`, `ADD_AN_AGENT.md`, `PACKAGING_PLAN.md`, `PROGRESS.md`, `VOICE_AUDIO_DIAGNOSTIC.md`, `helix_requirements.txt` | Same docs present but **untracked**; plus `consolidated_summary.md` |
| Feature evidence | `bridge/bridge_ws.py`, `bridge/helix_desktop.py`, `ui/src` (12 files), `tools/lms_client.py`, `install.sh`/`uninstall.sh` — all committed | Same files, uncommitted |
| Tool currency | Newer: `07a2522` adopted the shared JARVIS voice contract; `99c7a38` repointed the live diagnostic at the proxy's model | Older `tools/*` versions; 4 tool files locally edited beyond both commits |
| Deletion evidence | Deletions committed with rationale in `c68326b` | Deletions staged-but-uncommitted; **identical intent** |
| WIP genuinely at risk if abandoned | **None** (clean) | **5 files**: `.gitignore`, `tools/check-live.py`, `tools/helix_voice.py`, `tools/live_server.py`, `tools/live_tts.py` — plus 1 log file |
| Backup coverage | n/a (working tree) | `backup/HELIX-backup-20261109T211343Z-batch03`, **SHA256-verified, 808 files, HASH_MATCH** (B04) |

---

## 3. Determinations

### 3.1 Which line remains the immediate operational baseline?

**Line A — `AI_WORKSPACE/helix` @ `99c7a38`. `EVIDENCE-ESTABLISHED` (as the running source), `RECOMMENDED` (as the forward baseline).**

It is the only line the live service executes, the only clean line, the newer line, and the only one containing Line B's work plus two further refinements. There is no operational argument for Line B: switching to it would *downgrade* the running code and reintroduce 22 uncommitted deletions.

### 3.2 Should `/home/abubakargcx/helix` remain preserved as a research/refactor branch?

**Yes — preserve read-only. `RECOMMENDED`; disposal is `USER DECISION REQUIRED` (U5).**

But its status must be corrected in the record: it is **not** a competing refactor branch. It is a *stale working copy of `main` whose uncommitted changes are 93% already committed elsewhere*. Calling it a "development line" invites someone to develop on it and re-diverge.

Its only unique content is the 5 modified files listed above. Whether those edits are abandoned experiments or unfinished intent is a question only the author can answer.

### 3.3 What evidence is required before reconciliation?

Reconciliation here means "make `main`/`origin/main` reflect the consolidated state," which is a **git mutation** and therefore A3. Preconditions:

1. **Ratification (U4)** that `99c7a38` is the intended line of record.
2. **Diff review of the 5 Line-B files** (`U5`): each either already superseded by `07a2522`/`99c7a38`, or identified as content to carry forward. Currently `tools/live_server.py` differs in all three states (Line B working tree, `c68326b`, Line A HEAD), so it must be reviewed explicitly.
3. **Disposable-copy run evidence** (`HELIX_DISPOSABLE_VALIDATION.md`): the consolidated tree must at minimum import its entrypoints and build `ui/` without connecting to live services. Static inspection alone is insufficient to promote a branch.
4. **A stated branch policy** — whether `audit/consolidation-2026-11-06` is fast-forwarded into `main`, renamed, or kept as a permanent audit ref.
5. **Explicit A3 authorization** naming the refs and the direction of movement.

### 3.4 What must NOT be done yet

- Do **not** merge, rebase, cherry-pick, fast-forward, force-push, or delete any branch.
- Do **not** switch `helix-live.service` to `/home/abubakargcx/helix` — it is older, dirty, and untested as a service source.
- Do **not** `git checkout`/`restore`/`clean` inside `/home/abubakargcx/helix`; that would destroy the only unique content (the 5 modified files).
- Do **not** delete `/home/abubakargcx/helix`, the backup, or `BATCH_06/helix_home_disposable`.
- Do **not** push `audit/consolidation-2026-11-06` to `origin` — publishing an audit branch is an external, hard-to-reverse act.
- Do **not** treat the disposable copy as a development tree; it is evidence.

---

## 4. Consequences for the wider architecture

1. **"HELIX canonical tree" is no longer an open architectural question** — it is a *ref-topology* question (U4) plus a *5-file review* (U5). This is a material de-risking of the Batch 06 blocker Q603.
2. **The audit-branch pattern is ecosystem-wide.** HELIX and JARVIS both sit on `audit/consolidation-2026-11-06`, both consolidated on the same day, both with `main`/`master` left behind, and both with checkpoint commits named "pre-consolidation working state on an audit branch." This looks like one deliberate consolidation session, not two accidents — worth ratifying as a policy (one branch of record per project) rather than fixing per-repo.
3. **HELIX's `JARVIS_ROOT` dependency is real but no longer broken**, so HELIX↔JARVIS coupling exists at the voice-contract level (`07a2522`) and is a candidate for extraction later (D3) — after both trees stop moving.
