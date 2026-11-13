# Batch 02 Executive Summary — AJ Ecosystem Critical Infrastructure & Identity

**Date:** 2026-11-10 | **Mode:** Read-only, non-destructive (report files created only in `BATCH_02/`). No config/code/DB/service/permission/network changes, no installs/deletes/git mutations, no paid API tests, no UI automation. Secrets redacted.

## Bottom line
Batch 02 resolved the **most important P0 database ownership question** with strong evidence: Honcho (`localhost:8123`, healthy) targets the **system PostgreSQL 18** cluster on **port 5433**, database **`honcho`** (`honcho_local/honcho_server.py`). Dental Lounge Docker Postgres 17 instances on **5432/5434** are separate apps. However, **full Honcho schema/data ownership and Hermes→Honcho runtime writes remain unverified** due to privileged DB access limits and missing runtime trace.

**Canonical AJ/JARVIS source is NOT established.** `/home/abubakargcx/JARVIS` is missing; `AI_WORKSPACE/AJ` is an AJ control-plane foundation (non-git) distinct from legacy JARVIS app backups; two dirty JARVIS backups share the same HEAD and require preservation/full diff before any identity decision.

**HELIX is at preservation risk but recoverable in principle**: the worktree is dirty with major tracked deletions (bridge server, deploy unit, diagnostics, large UI areas) and **untracked replacement/WIP files** (`bridge_ws.py`, `helix_desktop.py`, new `ui/src` build structure, docs/scripts). **No git cleanup/restore performed.** Intent must be clarified and a full backup including untracked files should be approved.

**Security/network posture has notable exposures/unknowns**: external binds on 3389 (RDP), 5432/5434 (Docker DBs), and unexplained 8000/8765; `~/.hermes/honcho.json` is `664`. Hermes default inference is now OpenRouter (Batch 01 follow-up verified); OmniRush preserved.

## What changed from Batch 01 (now VERIFIED/strongly evidenced)
- Honcho’s **intended/observed backend target**: PG18 port 5433, db `honcho` (code + config + health).
- Docker Dental Lounge DB roles/DB names and volume ownership (metadata, redacted).
- Current port→process snapshot including helix-globe/helix-live/hermes/omnirush owners; identified external/exposed listeners.
- AJ/JARVIS candidates are **not interchangeable copies** (AJ foundation vs legacy JARVIS app backups).
- HELIX dirty state includes **untracked potential replacement code** — higher preservation urgency.

## Still ambiguous / blocked
- Canonical active AJ/JARVIS runtime and source of truth.
- Honcho DB schema/row-level ownership and actual Hermes/AJ/JARVIS/HELIX reads/writes.
- Owners/purpose of ports 8000 and 8765; intentionality/auth of exposed services.
- HELIX refactor intent and feature preservation mapping.
- PG18 cluster-wide DB inventory and backup/restore coverage.

## Urgent next actions (approval-gated where noted)
1. **A4:** non-destructive backup of `/home/abubakargcx/helix` including untracked files.
2. **A1:** runtime-to-repo mapping for AJ/JARVIS/Hermes/HELIX launchers/configs.
3. **A2:** privileged metadata-only audit of PG18:5433/Honcho (+ cluster inventory).
4. **A1:** trace Hermes Honcho plugin enablement/runtime flow; correlate to Honcho metadata.
5. **A1:** identify 8000/8765 owners; review exposure intent for 3389/5432/5434.
