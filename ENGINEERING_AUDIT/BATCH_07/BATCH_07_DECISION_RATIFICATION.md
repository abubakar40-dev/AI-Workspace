# Batch 07 — Decision Ratification

**Date:** 2026-11-10 · **Mode:** A1 read-only, A2 metadata-only, A4 disposable copies · **A3/GREEN SIGNAL: NOT granted**

This report separates what the audit **established**, what engineering **recommends**, what only the **user** can decide, and what is **deferred**. No recommendation in this document is an approval, and no approval is implied by repetition.

---

## 1. EVIDENCE-ESTABLISHED

Facts demonstrated by evidence, not preference. These are not decisions — they are the ground the decisions stand on.

| # | Fact | Source |
|---|---|---|
| E1 | `AI_WORKSPACE/AJ` is a foundation codebase with modules for permissions, capability, task, audit, config, contracts, orchestrator, agents, execution, providers, memory, calling, plus `config/capabilities.json` and 7 test modules. It is **not a git repository** and has **no runtime entrypoint** (no `main.py`, `__main__.py`, `cli.py`, `pyproject.toml`, `setup.py`). | `ls`, `find`, `git rev-parse` (B07) |
| E2 | AJ's own README states the intent directly: "AJ is the ecosystem's control plane… It is **not** a second assistant runtime," with `JARVIS` general-work sub-agent, `HELIX` calling/communications sub-agent, `Hermes` execution runtime "NOT ATTACHED, awaiting GREEN SIGNAL." | `AI/README.md` (B07) |
| E3 | AJ defines boundary dataclasses that already cross trust boundaries: `AgentRequest`/`AgentResult` (AJ↔JARVIS, AJ↔HELIX), `ExecutionRequest`/`Result` (AJ↔Hermes), `SkillSpec` with review states `draft→tested→reviewed→approved→rejected→revoked`. | `aj/contracts.py` (B07) |
| E4 | AJ's tests were **not executed** in B07: no `pytest` exists in system Python, `venv-honcho`, or the bundled Hermes Python; installing one is out of scope. The README's "65 tests" claim remains **UNVERIFIED at execution level**. | `python3 -m pytest` → `No module named pytest` (B07) |
| E5 | **`AI_WORKSPACE/JARVIS` exists and is a git repository** — 1.9 GB, 106 Python source files, remote-less, HEAD `d93c702`, branch `audit/consolidation-2026-11-06`, 2 untracked `chat_history/*.md`. This **corrects the Batch 05 assumption** that JARVIS source was only present as backups. | `git`, `du`, `find` (B07) |
| E6 | JARVIS's audit branch is **3 commits ahead of `master` (`cffa32d`)**: `fe1f911` checkpoint, `6ba652b` "Remove Brahma/smart-home code and add the policy, audit, confirmation and shared-voice core", `d93c702` "Drop JARVIS/tools copies of HELIX's voice and call tooling". | `git log master..audit/…` (B07) |
| E7 | Filtered source comparison `AI_WORKSPACE/JARVIS` vs `backup/JARVIS-nested-duplicate-20261106`: 197 vs 223 files, 187 common, **10 only in the working tree** (`core/policy.py`, `core/audit.py`, `core/capabilities.py`, `core/confirmation.py`, `config/__init__.py`, 2 chat-history files…), **36 only in the backup** (all under `brahma_connect/` and `actions/brahma_connect.py` — smart-home/device-control code removed on purpose). | `find`+`comm` (B07) |
| E8 | `jarvis-claude-gateway.service` is `enabled`, `inactive`, and its `ExecStart=/home/abubakargcx/JARVIS/scripts/start-claude-gateway.sh` points at a **path that does not exist**. The canonical JARVIS tree is now `AI_WORKSPACE/JARVIS`, which the unit does not reference. | `systemctl --user cat` (B07) |
| E9 | `helix-live.service` is a **user** unit (`~/.config/systemd/user/`), `active`, `enabled`, `HELIX_LIVE_PORT=8788`, bound 127.0.0.1, `ExecStart=…/AI_WORKSPACE/helix/tools/live_server.py`, and sets `JARVIS_ROOT=/run/media/abubakargcx/My Drive/AI_WORKSPACE/JARVIS` — a path that **now exists** (correcting B05's "missing JARVIS_ROOT" finding). | `systemctl --user cat` (B07) |
| E10 | **HELIX lineage is not a fork.** `AI_WORKSPACE/helix` is on branch `audit/consolidation-2026-11-06` at `99c7a38` and **contains** `e8a64cf`, the head of `/home/abubakargcx/helix`. Commits after it: `c68326b` "Checkpoint: pre-consolidation working state on an audit branch", `07a2522`, `99c7a38`. `main` and `origin/main` in that repo both still point at `e8a64cf`. | `git log e8a64cf..99c7a38`, `cat-file` (B07) |
| E11 | **Line B's uncommitted WIP is already committed in Line A's history.** Comparing all 75 Line-B working-tree files against the `c68326b` tree (node_modules excluded): **69 MATCH**, **5 DIFF** (`.gitignore`, `tools/check-live.py`, `tools/helix_voice.py`, `tools/live_server.py`, `tools/live_tts.py`), **1 ONLY_LINEB** (`logs/oci-a1-launch.log`). So the "preserved WIP" is not lost work — it is the checkpoint commit. | `git hash-object` vs `ls-tree c68326b` (B07) |
| E12 | Line B carries only 5 uncommitted modifications plus 22 staged-as-deleted tracked files against its own HEAD; Line A HEAD (`99c7a38`) still contains `bridge/bridge_ws.py`, `ui/src` (12 files), `tools/lms_client.py`, `docs/AGENT_ARCHITECTURE.md`. | `git status`, `ls-tree` (B07) |
| E13 | Honcho metadata is unchanged across B06→B07: `workspaces=2` (max `2026-11-09 23:10:54.276904`), `sessions=1` (max `2026-11-09 23:13:12.374012`), `peers=0`, `messages=0`, `conclusions=0`. | A2 `psql` counts (B07) |
| E14 | Hermes routing is `model.provider: openrouter`, `model.default: openrouter/auto`. `~/.hermes/honcho.json` is `HONCHO_BASE_URL=http://localhost:8123`, `HONCHO_ENVIRONMENT=local`, API key present (redacted). No local model server exists (no listener on 11434/1234/vLLM ports; `ollama` probe returned connection failure). | `config.yaml`, redacted JSON, `ss`/`curl` (B07) |
| E15 | Therefore **any correctly routed Hermes turn currently implies a paid OpenRouter call**, and the Batch 06 failure is explained: the observed turn used `provider=custom base_url=http://localhost:8123` (i.e. Honcho used as the LLM endpoint), with the config comment "Using local Honcho instance instead of OpenRouter" still present. | `agent.log`, `config.yaml` (B07) |
| E16 | Exposure state re-confirmed live: `8000` = `legacy-printer-app` PID 973 root, `0.0.0.0`+`::`; `8765` = `mamba_desktop --background` (PID 140470), `0.0.0.0`; `5432`/`5434` = Docker `thedentallounge-db-1` / `dental-lounge-ui-v2-db-1`, published on `0.0.0.0`+`::`; `3389` = `gnome-remote-desktop-daemon` (PID 140279). Ecosystem services `8123/8788/4173/20129/3000/3200` are all `127.0.0.1`. | `ss -ltnp`, `ps`, `docker ps` (B07) |

---

## 2. RECOMMENDED

Engineering positions supported by the evidence above. **These are proposals, not approvals.**

| # | Recommendation | Basis | Confidence |
|---|---|---|---|
| R1 | Adopt `AI_WORKSPACE/AJ` as the canonical AJ control-plane source, and treat "no entrypoint, no git repo" as a **gap to close**, not a defect that disqualifies it. | E1–E3 | High |
| R2 | Keep AJ a **control plane only**: it must not become a second assistant runtime, must not embed HELIX UI/voice code, and must not own Honcho's schema. | E2 | High |
| R3 | Adopt `AI_WORKSPACE/JARVIS` as the **canonical JARVIS source tree** — it is the only JARVIS tree that exists, is committed, and is ahead of `master`/backups. | E5–E7 | High |
| R4 | Treat the JARVIS smarthome/Brahma removal (`6ba652b`) as **deliberate scope reduction to preserve**, not as data loss to reverse. | E6–E7 | High |
| R5 | Treat `AI_WORKSPACE/helix` (`99c7a38`, audit branch) as the **immediate operational and forward-development baseline**, and retire the framing of `/home/abubakargcx/helix` as a competing "WIP line". | E10–E12 | High |
| R6 | Preserve `/home/abubakargcx/helix` read-only as a **reference working copy** until its 5 uncommitted file diffs are reviewed — that is the only genuinely uncommitted content. | E11–E12 | High |
| R7 | Keep **AJ raw-first canonical memory**; Honcho remains a candidate adapter/index. Message count 0 means Honcho has **never been proven to hold memory**. | E13 | High |
| R8 | Do **not** activate `jarvis-claude-gateway.service` in its current form: it targets a nonexistent path. Retargeting it is a service mutation → A3. | E8 | High |
| R9 | Treat `legacy-printer-app:8000`, `mamba_desktop:8765`, both Docker Postgres ports, and `3389` as **out-of-ecosystem exposure decisions for the user**, not ecosystem fixes to make unilaterally. | E16 | High |
| R10 | Run the Hermes→Honcho writer validation **only** as an approved, paid-call-authorized or locally-routed test; it cannot be executed under current authorization. | E14–E15 | High |

---

## 3. USER DECISION REQUIRED

Only items that cannot be inferred from evidence, because they encode intent, cost, or risk appetite.

| # | Decision | Options | Why it cannot be inferred | Blocks |
|---|---|---|---|---|
| U1 | **Approve or decline the Hermes→Honcho writer validation**, including its cost/routing basis. | (a) authorize one paid OpenRouter turn (~1 short call) for a synthetic probe; (b) authorize a temporary local/custom provider route for the probe (config mutation); (c) defer validation and accept "writer unproven" indefinitely; (d) declare Honcho non-canonical and skip validation. | Requires spending money or mutating config; neither is inferable. | Honcho adapter status; memory confidence |
| U2 | **AJ runtime activation scope** — approve that Batch 08 may create an entrypoint/CLI inside `AI_WORKSPACE/AJ`. | (a) approve interface-only work (no process); (b) approve a local CLI entrypoint, no daemon; (c) approve CLI + supervised user service. | Decides whether a new runnable process exists on the machine. | Foundation plan |
| U3 | **JARVIS canonical-tree ratification** — confirm `AI_WORKSPACE/JARVIS` (audit branch) as canonical, and whether `master` should later fast-forward to it. | (a) ratify audit branch as canonical, defer `master` movement; (b) ratify and fast-forward `master` later (A3); (c) keep dual-track. | Branch promotion strategy is project policy. | JARVIS roadmap |
| U4 | **HELIX lineage ratification** — confirm the consolidation branch as the line of record, and whether `main`/`origin/main` should eventually be advanced from `e8a64cf`. | (a) ratify as-is, no ref movement; (b) plan a later fast-forward of `main` (A3, git mutation); (c) keep audit branch permanently. | Ref topology is a human policy choice. | HELIX roadmap |
| U5 | **Fate of `/home/abubakargcx/helix`'s 5 uncommitted file diffs** — are they abandoned experiments or content to carry forward? | (a) discard after review; (b) cherry-pick selected hunks later; (c) keep indefinitely as read-only reference. | Only the author knows intent. | HELIX cleanliness |
| U6 | **Exposure intent** for `8000`, `8765`, `3389`, `5432`, `5434`: is LAN/remote reachability required? | per-port keep/restrict/disable | Depends on the user's actual remote-use needs. | Security posture |
| U7 | **Whether Honcho should be retained at all** if it never becomes a writer target (it currently stores nothing). | (a) retain as future adapter; (b) retire service (A3); (c) repurpose. | Product intent. | Infra inventory |

---

## 4. DEFERRED

Intentionally postponed; no action now, no approval implied.

| # | Item | Why deferred |
|---|---|---|
| D1 | AJ `master`-branch/git initialisation, packaging (`pyproject.toml`), CI | Blocked behind U2 (runtime scope) |
| D2 | Memory migration, backfill, or Honcho schema work | Depends on U1/U7 |
| D3 | HELIX ↔ JARVIS shared voice-contract extraction into a package | Both trees just consolidated; premature extraction freezes unstable surfaces |
| D4 | GUI, voice, browser/desktop/LMS automation, robotics, smart-home | Explicitly out of foundation scope |
| D5 | Containerising AJ/Honcho, remote deployment, custom domains | No runtime to deploy yet |
| D6 | Reconciliation merge of any two repositories | No evidence requires it; line A already contains line B's work |
| D7 | Restoring Brahma/smart-home code | Deliberately removed; restoration contradicts ratified scope reduction |
| D8 | Obsidian/backlink navigation layer over canonical memory | Downstream of the memory contract being implemented |
