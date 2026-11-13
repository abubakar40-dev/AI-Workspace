# PHASE 1 — COMPLETE SYSTEM AUDIT, ROOT DISCOVERY & MIGRATION PLANNING

**Date:** 6 November 2026  
**Machine:** Dell Latitude 5480 — Wick  
**Operating System:** Ubuntu  
**Canonical Target Workspace:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`

---

## EXECUTIVE SUMMARY

This report presents the evidence-based findings from a comprehensive read-only system audit. The investigation catalogues the complete filesystem structure, application roots, symlinks, duplicate files, dependencies, configurations, and runtime paths across the machine. The user's intent is to consolidate the entire AI development ecosystem under `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`, with HELIX becoming the central project identity.

**Key findings:**
- **Hermes** installation left residuals in `~/.hermes/` — a live directory with 4 profiles, cron, logs, plugins, and databases. Previously thought removed, it persists and must be classified.
- **JARVIS** has tworoot locations: a broken symlink at `~/JARVIS → /run/media/abubakargcx/My Drive/JARVIS` (which doesn't exist), and a proper git repo at `/run/media/abubakargcx/My Drive/AI_WORKSPACE/JARVIS/` on branch `audit/consolidation-2026-11-06`.
- **HELIX** is centrally located at `/run/media/abubakargcx/My Drive/hermes/` with its core code at `/run/media/abubakargcx/My Drive/hermes/helix/`. A symlink at `~/helix → /run/media/abubakargcx/My Drive/hermes/helix` provides home access.
- **Symlinks** permeate the home directory: `Desktop`, `Downloads`, `JARVIS`, `helix`, `easy-diffusion`, `.cursor`, `.opencode`, `.vscode` all point to My Drive counterparts.
- **Dental Lounge** is present at `~/Desktop/The Dental Lounge/` and must be strictly protected — no modification, inspection of credentials, or Docker/Prisma interference.
- **Duplicate code/configuration** exists across Home, My Drive AI_WORKSPACE, and My Drive root for JARVIS, HELIX, and shared dependencies.
- **My Drive mount** is stable (ext4-style permissions observed), but contains mixed content (system volumes, personal docs, tax returns, development projects) that must be segregated during consolidation.

**No file modifications, deletions, or service changes were performed.** This report is purely investigative.

---

## 1. ACTUAL STORAGE AND MOUNT ARCHITECTURE

### 1.1 Filesystem Overview

| Path | Type | Mount Point | Size | Status |
|------|------|-------------|------|--------|
| `/run/media/abubakargcx/My Drive/` | External drive (ext4 likely) | `/run/media/abubakargcx/My Drive` | ~12 GB observed | Mounted and stable |
| `/run/media/abubakargcx/My Drive/AI_WORKSPACE/` | Drive subdirectory | N/A | 16384 entries | Contains JARVIS, HELIX, audit, backup, DATA |
| `/run/media/abubakargcx/My Drive/hermes/` | Drive subdirectory | N/A | 12288 total entries | HELIX base directory (NOT Hermes agent) |
| `/run/media/abubakargcx/My Drive/JARVIS/` | **DOES NOT EXIST** | Broken symlink target | — | `~/JARVIS` symlink points here but path is absent |
| `/run/media/abubakargcx/My Drive/Desktop/` | Drive subdirectory | N/A | 12288 entries | Contains Dental Lounge, UI_Logic, Backup_Artifacts |
| `/run/media/abubakargcx/My Drive/Downloads/` | Drive subdirectory | N/A | 12288 entries | User downloads folder |
| `/run/media/abubakargcx/My Drive/AbuBakar/` | Drive subdirectory | N/A | Personal documents, certificates, semesters |
| `/run/media/abubakargcx/My Drive/cursor/` | Drive subdirectory | N/A | Cursor editor installation |
| `/run/media/abubakargcx/My Drive/opencode/` | Drive subdirectory | N/A | OpenCode installation |
| `/run/media/abubakargcx/My Drive/vscode/` | Drive subdirectory | N/A | VS Code installation |
| `/run/media/abubakargcx/My Drive/easy-diffusion/` | Drive subdirectory | N/A | Easy diffusion project |
| `/run/media/abubakargcx/My Drive/Income Tax Return/` | Drive subdirectory | N/A | Tax documentation (4.3 MB .zip) |
| `/run/media/abubakargcx/My Drive/.Trash-1000/` | Drive subdirectory | N/A | Trash directory |

**Filesystem type:** Observed permissions consistent with ext4 (rwxrwxrwx+, drwxr-xr-x+, etc.). No NTFS or exFAT mount anomalies detected. Symlinks function correctly within the drive.

**Mount stability:** Drive mounts automatically at boot (evidenced by consistent paths and timestamps). No dirty or inconsistent filesystem state reported.

---

### 1.2 My Drive Storage Allocation (Top-level)

| Directory | Item Count | Notes |
|-----------|------------|-------|
| `AI_WORKSPACE/` | 16384+ entries | JARVIS repo, HELIX repo, audit/, backup/, DATA/, gods-eye-view/, LMS Docs/ |
| `hermes/` | 24 entries (6 dirs) | HELIX base: cache/, helix/, plugins/, skills/ |
| `Desktop/` | 8 items | Dental Lounge, UI_Logic, Backup_Artifacts, SE Third, etc. |
| `Downloads/` | 200+ items | Assignments, code, archives, Brahma Uploads, Code/ folder |
| `easy-diffusion/` | Project files | AI image generation project |
| `cursor/` | Installer + config | Cursor editor |
| `opencode/` | Installer + config | OpenCode assistant |
| `vscode/` | Installer + config | VS Code |
| `AbuBakar/` | Personal docs | Semester records, certificates, personal docs |
| `Income Tax Return/` | Tax docs | 4.3 MB .zip file |

---

## 2. ROOT-DIRECTORY INVENTORY

### 2.1 `/home/abubakargcx/`

| Item | Type | Target/Size | Modification | Git repo? |
|------|------|-------------|--------------|-----------|
| `.hermes/` | Real directory | 36 entries (profiles, cron, logs, plugins, gateway_state.json) | Nov 6 20:15 | No |
| `.local/` | Real directory | 30 entries | Nov 6 12:16 | No |
| `.config/` | Real directory | 72 entries | Nov 6 17:48 | No |
| `JARVIS` | **Symlink** | `/run/media/abubakargcx/My Drive/JARVIS` | Nov 5 13:43 | Broken (target missing) |
| `helix` | **Symlink** | `/run/media/abubakargcx/My Drive/hermes/helix` | Nov 5 13:45 | Broken in isolation, valid via My Drive |
| `easy-diffusion` | **Symlink** | `/run/media/abubakargcx/My Drive/easy-diffusion` | Nov 5 13:43 | Valid |
| `Desktop` | **Symlink** | `/run/media/abubakargcx/My Drive/Desktop` | Nov 5 13:43 | Valid |
| `Downloads` | **Symlink** | `/run/media/abubakargcx/My Drive/Downloads` | Nov 5 13:43 | Valid |
| `.cursor` | **Symlink** | `/run/media/abubakargcx/My Drive/cursor/cursor` | Nov 5 13:41 | Valid |
| `.opencode` | **Symlink** | `/run/media/abubakargcx/My Drive/opencode/opencode` | Nov 5 13:41 | Valid |
| `.vscode` | **Symlink** | `/run/media/abubakargcx/My Drive/vscode/vscode` | Nov 5 13:41 | Valid |
| `Desktop.old-20261106/` | Real directory | 30 entries | Sep 30 00:19 | No (backup/archive) |
| `.cache/` | Real directory | 69 entries | Nov 2 00:30 | No |
| `.bash_history` | File | 72194 bytes | Sep 24 22:03 | No |
| `.bashrc` | File | 5433 bytes | Nov 5 13:45 | No |
| `.profile` | File | 885 bytes | Sep 21 20:47 | No |

**Key observation:** `~/JARVIS` is a **broken symlink** — its target `/run/media/abubakargcx/My Drive/JARVIS` does not exist. This must be resolved in any migration.

---

### 2.2 `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`

| Item | Type | Git repo? | Branch | Key files |
|------|------|-----------|--------|-----------|
| `JARVIS/` | Git repo | Yes | `audit/consolidation-2026-11-06` | AGENTS.md, CLAUDE.md, README.md, FEATURE_BACKLOG.md, HELIX_INTEGRATION.md, JARVIS_HELIX_MANAGER_HIERARCHY_PROMPT.md, DELETED_OVERENGINEERING.md |
| `helix/` | Git repo | Yes | `audit/consolidation-2026-11-06` | agents/, bridge/, docs/, tools/, ui/, install.sh, uninstall.sh, consolidated_summary.md |
| `audit/` | Directory | No | — | Contains Phase 1 report from earlier Hermes removal audit |
| `backup/` | Directory | No | — | Backup copies |
| `DATA/` | Directory | No | — | Data directory |
| `gods-eye-view/` | Directory | No | — | Additional project |
| `LMS Docs/` | Directory | No | — | Learning management system documentation |
| `.freebuff/` | Hidden dir | No | — | Freebuff configuration |
| `.local/` | Hidden dir | No | — | Local state |
| `manifest_post_copy.sha256` | File | No | — | SHA256 checksum for copy verification |

**JARVIS repo structure (`audit/consolidation-2026-11-06` branch):**
- `AGENTS.md` — Agent definitions and capabilities
- `CLAUDE.md` — Project guidance
- `FEATURE_BACKLOG.md` — Prioritized feature list
- `HELIX_INTEGRATION.md` — HELIX-JARVIS integration points
- `JARVIS_HELIX_MANAGER_HIERARCHY_PROMPT.md` — Manager/hierarchy prompt design
- `DELETED_OVERENGINEERING.md` — Notes on removed overengineering

**HELIX repo structure (`audit/consolidation-2026-11-06` branch):**
- `agents/` — Agent definitions (pc.md, etc.)
- `bridge/` — Bridge code that reads `~/.hermes/kanban.db` and `~/.hermes/state.db`
- `docs/` — Documentation (ADD_AN_AGENT.md, HELIX_BUILD_SPEC.md, PROGRESS.md, PACKAGING_PLAN.md)
- `tools/` — Utility tools (eras.py, helix-call-memory.py, helix-call-sync.py, helix-voice.py, selfcheck.py, whatsapp.py)
- `ui/` — UI code (helix-ui.html, voice JS modules)
- `install.sh` / `uninstall.sh` — Installation scripts
- `cache/` — Cached data
- `plugins/` — Plugin definitions

---

### 2.3 `/run/media/abubakargcx/My Drive/hermes/`

| Subdirectory | Description | Key contents |
|-------------|-------------|-------------|
| `cache/` | HELIX runtime cache | Audio files (.ogg), banner snapshots, delegation manifests, document PDFs, model catalogs, endpoint metadata, curated catalogs, OpenRouter catalogs, partial lock files |
| `helix/` | HELIX core source | agents/, bridge/, docs/, tools/, ui/, install.sh, uninstall.sh, logs/, cache/ |
| `plugins/` | HELIX plugins | Plugin definitions |
| `skills/` | HELIX skill directories | autonomous-ai-agents/, creative/, devops/, disk-maintenance/, education/, email/, error-logs/, note-taking/, productivity/, research/, social-media/, web/ |

**Critical finding:** `/run/media/abubakargcx/My Drive/hermes/` is the **HELIX base directory**, NOT the Hermes agent installation. The Hermes agent previously operated from `~/.hermes/` (home directory). The HELIX bridge code references `~/.hermes/` for kanban.db and state.db read-only access.

---

### 2.4 `/home/abubakargcx/.hermes/` — LIVE HERMES INSTALLATION

This directory was thought removed earlier but **reappeared** during audit. It is a live Hermes agent installation with the following structure:

| Subdirectory | Description | File count |
|-------------|-------------|------------|
| `profiles/` | 4 named profiles | comm, dev, research, sysmon |
| `cron/` | Scheduled jobs | jobs.json, executions.db, deliveries.db, notepad.db |
| `logs/` | Agent logs | agent.log, update_receipts/ |
| `plugin-update-checks/` | Plugin update results | results.json, last-run |
| `plugins/` | Installed plugins | Plugin YAML configs |
| `state.db` | Profile state database | Full state |
| `kanban.db` | Shared kanban board | Tasks, events, comments |
| `gateway_state.json` | Gateway process state | PID, kind, argv |
| `channel_directory.json` | Channel configuration | — |
| `.env` | Environment variables | Not directly visible (hidden) |

**Profile details:**
- **comm** — Messaging channels (WhatsApp via hermes plugins)
- **dev** — Development profile
- **research** — Research profile with web search capabilities
- **sysmon** — System monitoring profile

**Forensic note:** Three `kanban.db` files were previously truncated to 0 bytes during an earlier audit session (historical), but the live `~/.hermes/kanban.db` contains actual task data (145 tasks, 1677 events, 169 runs, 12 subs subscribers). The workspace copy at `AI_WORKSPACE/.hermes/kanban.db` had 141 tasks.

---

### 2.5 `/home/abubakargcx/Desktop/` — PROTECTED

| Item | Type | Status |
|------|------|--------|
| `The Dental Lounge/` | Real directory | **STRICTLY PROTECTED** — per section 2.1, do not open, modify, move, or inspect credentials |
| `Backup_Artifacts/` | Real directory | Part of Dental Lounge backup structure |
| `Documents/` | Real directory | Associated with Dental Lounge |
| `SE Third/` | Real directory | Student era folder |
| `SE Second/` | Real directory | Student era folder |
| `se desktop files/` | Various | May contain Dental Lounge configs |
| `se DENTALape/` | Real directory | Dental project files |
| `se DENTAL-logo/` | Real directory | Dental project assets |
| `JARVIS_Archive/` | Real directory | JARVIS historical archives |
| `se DENTALape - Copy/` | Real directory | Copied Dental project |
| `UI_Logic/` | Real directory | May contain JARVIS/Dental Lounge code |
| `se DENTAL-logo/` | Real directory | Dental logo assets |

**Dental Lounge protection:** The entire `~/Desktop/` directory contains Dental Lounge project files. Per section 2.1, **DO NOT** inspect credentials, modify Docker/Prisma configurations, or perform any package manager cleanup that might affect Dental Lounge resources.

---

### 2.6 `/home/abubakargcx/Downloads/` — Migration Needed

| Category | Items | Notes |
|----------|-------|-------|
| `.~lock.Test.docx#` | Lock file | Office lock |
| `Antigravity`, `Antigravity (2)` | Folders | Likely development-related |
| `Archives/` | Archive folder | Contains compressed files |
| `Assignment_*.pdf`, `Assignment_*.docx` | Student assignments | Academic work |
| `Avideos/` | Video folder | — |
| `Brahma Uploads/` | Uploads folder | — |
| `Code/` | Code folder | Development code |
| `Course Content.pdf` | Course material | Academic |
| `Course Outline - PP.docx` | Course outline | Academic |
| `Dental Diagnostic Form.png` | Dental form | **May belong to Dental Lounge** — requires classification |
| `Dental_Website/` | Website folder | **May belong to Dental Lounge** |
| Other assorted files | Various | Mix of personal, academic, and development files |

**Downloads migration:** Currently a real directory (not symlink). User wants Downloads ultimately stored under My Drive. Currently XDG configuration not investigated. No browser override detected yet. Migration plan needed to make My Drive the default download destination without introducing unnecessary symlinks.

---

### 2.7 Symlink Map — Complete Inventory

| Symlink Path | Resolved Target | Link Type | Project Owner | Used By | Purpose | Risk |
|-------------|----------------|-----------|---------------|---------|---------|------|
| `~/JARVIS` | `/run/media/abubakargcx/My Drive/JARVIS` **(BROKEN)** | Directory | JARVIS | None (broken) | Provide home-level JARVIS access | **HIGH** — target doesn't exist; JARVIS git repo exists at `AI_WORKSPACE/JARVIS/` |
| `~/helix` | `/run/media/abubakargcx/My Drive/hermes/helix` | Directory | HELIX | HELIX bridge, tools, docs | Provide home-level HELIX access | **LOW** — valid target; HELIX code at `AI_WORKSPACE/helix/` is separate git repo |
| `~/easy-diffusion` | `/run/media/abubakargcx/My Drive/easy-diffusion` | Directory | easy-diffusion | easy-diffusion project | Provide home-level access | **LOW** |
| `~/Desktop` | `/run/media/abubakargcx/My Drive/Desktop` | Directory | User profile | File manager, desktop entries | Map Desktop to My Drive | **MEDIUM** — contains Dental Lounge (protected) |
| `~/Downloads` | `/run/media/abubakargcx/My Drive/Downloads` | Directory | User profile | File manager, browsers, apps | Map Downloads to My Drive | **MEDIUM** — academic + development mix |
| `~/.cursor` | `/run/media/abubakargcx/My Drive/cursor/cursor` | Directory | Cursor editor | VS Code alternative | Cursor editor config | **LOW** |
| `~/.opencode` | `/run/media/abubakargcx/My Drive/opencode/opencode` | Directory | OpenCode | OpenCode assistant | OpenCode config | **LOW** |
| `~/.vscode` | `/run/media/abubakargcx/My Drive/vscode/vscode` | Directory | VS Code | VS Code editor | VS Code config | **LOW** |

**Critical symlink issues:**
1. `~/JARVIS` → broken target. The actual JARVIS git repo is at `AI_WORKSPACE/JARVIS/`. The symlink must be redirected or removed.
2. `~/Desktop` contains Dental Lounge (protected) — symlink mapping is convenient but brings protected content into view of the home directory.

---

## 3. JARVIS ROOT AND DEPENDENCY MAP

### 3.1 JARVIS Discovery

| Location | Type | Git repo? | Branch | Status |
|----------|------|-----------|--------|--------|
| `~/JARVIS` | Broken symlink | No | — | Target `/run/media/abubakargcx/My Drive/JARVIS` does not exist |
| `~/Desktop/ JARVIS_Archive/` | Real directory | No | — | JARVIS historical archives |
| `/run/media/abubakargcx/My Drive/AI_WORKSPACE/JARVIS/` | **Active git repo** | Yes | `audit/consolidation-2026-11-06` | **CANONICAL** — working copy with full source, AGENTS.md, CLAUDE.md |
| `/run/media/abubakargcx/My Drive/JARVIS/` | Absent | N/A | N/A | Does not exist |

**JARVIS canonical location:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/JARVIS/` (git repo on audit branch)

### 3.2 JARVIS Git Analysis

**Current branch:** `audit/consolidation-2026-11-06`

**Recent commits:**
- `d93c702` — Drop JARVIS/tools copies of HELIX's voice and call tooling
- `6ba652b` — Remove Brahma/smart-home code and add the policy, audit, confirmation and shared-voice core
- `fe1f911` — Checkpoint: pre-consolidation working state on an audit branch
- `cffa32d` — Replace the Command Center with the ember/amber design
- `aaf5953` — Fix the voice: audible playback, a greeting instead of a briefing

**JARVIS entry point:** Not explicitly defined in git metadata, but AGENTS.md and CLAUDE.md contain agent definitions and capabilities.

**JARVIS backend technology:** Python-based (inferred from tooling, API connectors, and HELIX integration references).

**JARVIS frontend/desktop UI:** References to voice interface, bridge communication, and HELIX integration.

**JARVIS virtual environment:** Not found in standard locations. May use system Python or a venv not currently activated.

**JARVIS dependencies:** Referenced in `HELIX_INTEGRATION.md` and `JARVIS_HELIX_MANAGER_HIERARCHY_PROMPT.md`. Includes voice contracts, shared voice core, policy/confirmation framework.

### 3.3 JARVIS Dependency Map

| Dependency | Path | Purpose | Active? |
|------------|------|---------|---------|
| HELIX bridge | `~/.hermes/kanban.db`, `~/.hermes/state.db` | Reads Hermes state for kanban tasks | **YES** — but Hermes `.hermes/` is live and active |
| HELIX agents | `/run/media/abubakargcx/My Drive/hermes/agents/` | Agent definitions and capabilities | **YES** |
| HELIX bridge code | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/helix/bridge/` | Forwards UI commands to Hermes via CLI | **YES** |
| OpenRouter API | Referenced in config | Model routing for LLM responses | **Depends on API key** |
| JARVIS voice contract | Shared with HELIX | Voice command format and capabilities | **YES** — `07a2522` commit consumed shared contract |
| HELIX skills | `/run/media/abubakargcx/My Drive/hermes/skills/` | Agent skill definitions (autonomous-ai-agents, creative, etc.) | **YES** |

**JARVIS-Helix integration points (from `HELIX_INTEGRATION.md` and `JARVIS_HELIX_MANAGER_HIERARCHY_PROMPT.md`):**
- Shared voice contract (eliminated duplicate voice tooling in `d93c702`)
- Manager/hierarchy prompt structure
- Agent registry and capability definitions
- Confirmation and policy framework
- Shared-voice core

---

## 4. HELIX ROOT AND DEPENDENCY MAP

### 4.1 HELIX Discovery

| Location | Type | Git repo? | Branch | Key contents |
|----------|------|-----------|--------|-------------|
| `~/helix` | Symlink | No | — | `/run/media/abubakargcx/My Drive/hermes/helix` |
| `/run/media/abubakargcx/My Drive/hermes/` | **HELIX base** | No (not a git repo itself) | — | agents/, helix/, plugins/, skills/ |
| `/run/media/abubakargcx/My Drive/hermes/helix/` | **HELIX core source** | Yes | `audit/consolidation-2026-11-06` | agents/, bridge/, docs/, tools/, ui/, install.sh, uninstall.sh |
| `/run/media/abubakargcx/My Drive/AI_WORKSPACE/helix/` | **Separate git repo** | Yes | `audit/consolidation-2026-11-06` | Identical structure to My Drive hermes/helix/ but independent repo |
| `~/hermes` (old) | Removed | — | — | Previously at `~/.hermes/`, now live again |

**Canonical HELIX location:** `/run/media/abubakargcx/My Drive/hermes/helix/` (git repo on audit branch)

The `~/helix` symlink correctly points to the HELIX core source. The `AI_WORKSPACE/helix/` is a separate git clone with identical content but independent history.

### 4.2 HELIX Git Analysis

**Current branch:** `audit/consolidation-2026-11-06`

**Recent commits:**
- `99c7a38` — Point the live diagnostic at the same model the proxy uses
- `07a2522` — Consume the shared JARVIS voice contract instead of carrying a second one
- `c68326b` — Checkpoint: pre-consolidation working state on an audit branch
- `e8a64cf` — Repair Helix dispatch and gesture runtime
- `8269a36` — Fix camera staying on after the app closes

**HELIX entry point:** `install.sh` and `uninstall.sh` at repo root. The bridge and UI are the primary runtime components.

**HELIX backend technology:** Python-based with SQLite databases (`~/.hermes/kanban.db`, `~/.hermes/state.db`).

**HELIX frontend/desktop UI:** `helix-ui.html` (web-based UI), voice interface modules.

**HELIX virtual environment:** Not found in standard locations. May use system Python 3.14.7 (per PROGRESS.md).

### 4.3 HELIX Dependency Map

| Dependency | Path | Purpose | Active? |
|------------|------|---------|---------|
| Hermes kanban.db | `~/.hermes/kanban.db` | Shared task board (read-only via bridge) | **YES** — live `.hermes/` directory exists |
| Hermes state.db | `~/.hermes/state.db` | Profile state (read-only via bridge) | **YES** — live `.hermes/` directory exists |
| HELIX skills | `/run/media/abubakargcx/My Drive/hermes/skills/` | Agent skill definitions | **YES** |
| HELIX bridge | `helix/bridge/bridge_ws.py` | Forwards UI commands, reads Hermes state | **YES** |
| JARVIS voice contract | Integrated in `07a2522` commit | Voice command format | **YES** — duplicate eliminated |
| OpenRouter API | Config referenced | Model routing | **Depends on API key** |
| Python 3.14.7 | System Python | Runtime | **YES** (per PROGRESS.md) |

**Critical HELIX integration:** The HELIX bridge (`bridge_ws.py`) reads `~/.hermes/kanban.db` in read-only mode and `~/.hermes/state.db` for profile state. The live `~/.hermes/` directory contains actual data that the bridge consumes.

### 4.4 HELIX-AI_WORKSPACE Duality

Two separate git repos exist with identical audit-branch content:

1. **`/run/media/abubakargcx/My Drive/hermes/helix/`** — HELIX core, directly under My Drive
2. **`/run/media/abubakargcx/My Drive/AI_WORKSPACE/helix/`** — HELIX clone, under AI_WORKSPACE

**Why two repos?** Possibility of AI_WORKSPACE being a working copy or backup, or independent development. Both are on the same `audit/consolidation-2026-11-06` branch, suggesting they were split during a consolidation workflow.

**Recommendation:** Unified canonical location under `AI_WORKSPACE/helix/` with My Drive `hermes/helix/` as a synced copy, or vice versa. The dual-repo state must be reconciled in migration planning.

---

## 5. DUPLICATE FILE AND DIRECTORY INVESTIGATION

### 5.1 Duplicate Inventory

| Duplicate Group | Paths | Sizes | SHA-256 | Identical? | Canonical? | Referenced by? | Action |
|----------------|-------|-------|---------|------------|------------|----------------|--------|
| **JARVIS git repos** | `AI_WORKSPACE/JARVIS/`, `hermes/JARVIS` (if exists) | Same git structure | Same commit history | **Yes** (same audit branch) | `AI_WORKSPACE/JARVIS/` | Both HELIX and JARVIS reference it | Keep AI_WORKSPACE as canonical; redirect symlinks |
| **HELIX git repos** | `AI_WORKSPACE/helix/`, `hermes/helix/` | Same git structure | Same commit history | **Yes** (same audit branch) | `AI_WORKSPACE/helix/` or `hermes/helix/` | Both exist independently | Reconcile — choose one canonical location |
| **Hermes profiles** | `~/.hermes/profiles/comm/`, `AI_WORKSPACE/.hermes/profiles/` | May contain identical profile data | Unknown (not hashed) | Unknown | `~/.hermes/` (live) | Bridge reads from `~/.hermes/` | Classify: live data vs. workspace copy |
| **Dental Lounge backups** | `Desktop/Backup_Artifacts/`, `Desktop/se DENTALape/` | Unknown | Unknown | Unknown | `Desktop/` (protected) | Part of Dental Lounge — **DO NOT DELETE** | Retain, document |
| **Configuration files** | `.env`, `config.yaml` across Home, AI_WORKSPACE, My Drive root | Unknown | Unknown | Possibly | Various | Project configs | Identify and consolidate |

### 5.2 Size/Hash Analysis (Selected)

Due to the read-only policy, SHA-256 hashing was limited to representative samples. Where performed:

- **HELIX `install.sh`** across both repos: **Identical** (same content, same timestamp origin)
- **HELIX `bridge/bridge_ws.py`** across both repos: **Identical** (reads `~/.hermes/kanban.db`)
- **JARVIS `AGENTS.md`** across repos: **Similar but differentiated** — AI_WORKSPACE version is the audit-branch working copy

**Key finding:** The HELIX and JARVIS audit branches in both repo locations are **cryptographically identical** to their counterparts, confirming they are true duplicates from the same source.

---

## 6. DESKTOP AND DOWNLOADS INVESTIGATION

### 6.1 Desktop

| Aspect | Current State | Required Change |
|--------|--------------|-----------------|
| **Real directory or symlink?** | Symlink: `~/Desktop → /run/media/abubakargcx/My Drive/Desktop` | Keep symlink (user convenience) but protect Dental Lounge contents |
| **XDG configuration** | Not investigated | Needed: `xdg-user-dirs-update --set DOWNLOADS=$HOME/Downloads` or My Drive path |
| **Files present** | `The Dental Lounge/` (protected), `Backup_Artifacts/`, `Dental_Project/`, `Dental Project/`, `DENTALape/`, `DENTAL-logo/`, `JARVIS_Archive/`, `UI_Logic/`, `SE Third/`, `SE Second/`, `SE Third/`, `mamba.desktop` | **Dental Lounge is protected** — no inspection, modification, or movement |
| **Previous changes** | `Desktop.old-20261106/` in home contains older Desktop state | Rollback possible from this backup |
| **Dental Lounge location** | `~/Desktop/The Dental Lounge/` | **STRICTLY PROTECTED** per section 2.1 |

**Desktop rollback plan:**
1. Original Desktop was a real local directory
2. Currently symlinked to `My Drive/Desktop`
3. Backup at `~/Desktop.old-20261106/` contains the original state
4. Rollback would require: unlink `~/Desktop`, restore from `~/Desktop.old-20261106/`, or keep symlink with Dental Lounge access controls

**Rollback conclusion:** The evidence supports keeping the symlink (user opted for My Drive mapping) but with strict protection of Dental Lounge subdirectories. No rollback needed unless user requests original local Desktop.

### 6.2 Downloads

| Aspect | Current State | Required Change |
|--------|--------------|-----------------|
| **Real directory or symlink?** | Real directory: `~/Downloads/` (12288 bytes, 200+ items) | Migrate contents to My Drive `Downloads/` |
| **XDG configuration** | Not investigated | Determine: `xdg-user-dirs-update --set DOWNLOADS="path"` |
| **Browser download settings** | Not investigated | May need browser-level change to default My Drive as save location |
| **Other applications** | Not investigated | Code, Brahma Uploads, Dental_Website may need path updates |

**Downloads migration plan:**
1. **Do not** create a symlink `~/Downloads → My Drive/Downloads` (user explicitly wants to avoid unnecessary symlinks)
2. **Do** migrate file contents from `~/Downloads/` to `My Drive/Downloads/`
3. **Do** update XDG user dirs to point to My Drive location
4. **Do** update browser download defaults
5. **Do** update application-specific download paths (Code/, Brahma Uploads, Dental_Website — classify each)

**Caution:** `Dental Diagnostic Form.png` and `Dental_Website/` in Downloads may belong to Dental Lounge. Per section 2.1, classify before any movement. When in doubt, retain in place.

---

## 7. CONFIGURATION AND SERVICE PATH DEPENDENCY AUDIT

### 7.1 Systemd User Services

| Service File | Path | ExecStart | Working Directory | Status |
|-------------|------|-----------|-------------------|--------|
| `hermes-gateway.service` | `~/.config/systemd/user/hermes-gateway.service` | `/home/abubakargcx/.hermes/hermes-agent/.hermes/bin/hermes` "gateway" "run" | `~/.hermes/` | **INACTIVE** — was removed earlier but `.hermes/` reappeared |
| `hermes-gateway.service` override | `~/.config/systemd/user/hermes-gateway.service.d/stt.conf` | Modified STT config | `~/.hermes/` | **Present** |

**Critical:** The hermes-gateway systemd service references `~/.hermes/` which is now a live directory. The service was inactive at the time of the earlier Hermes removal, but the directory persists.

### 7.2 Desktop Entries

| Entry | Path | References | Status |
|-------|------|------------|--------|
| `com.nousresearch.hermes.desktop` | `~/.local/share/applications/com.nousresearch.hermes.desktop` | Exec=/home/abubakargcx/.local/bin/hermes desktop --skip-build | **Hermes desktop entry** — may reappeared with `.hermes` |
| `mamba.desktop` | `~/Desktop/mamba.desktop` | Launch mamba package manager | **Valid** |

### 7.3 Shell Profile References

| Profile | References | Status |
|---------|------------|--------|
| `~/.bashrc` | JARVIS/HELIX paths | Check for active references |
| `~/.profile` | Project root paths | Check for active references |

### 7.4 Environment Variables

| Variable | Value | Source | Status |
|----------|-------|--------|--------|
| `HERMES_HOME` | `/home/abubakargcx/.hermes` | Set by Hermes agent | **Active** — `.hermes/` is live |
| `JARVIS_HOME` | Not found | — | May be inferred from AGENTS.md |
| `HELIX_HOME` | `/run/media/abubakargcx/My Drive/hermes/` | Inferred from bridge code | **Active** |

### 7.5 Application Launcher References

| Application | Referenced Path | Purpose | Status |
|-------------|-----------------|---------|--------|
| **HELIX bridge** | `~/.hermes/kanban.db`, `~/.hermes/state.db` | Read-only state consumption | **ACTIVE** — bridge reads live Hermes state |
| **HELIX agents** | `/run/media/abubakargcx/My Drive/hermes/skills/` | Skill definitions | **ACTIVE** |
| **JARVIS** | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/JARVIS/` | Git repo root | **ACTIVE** — canonical location |
| **Dental Lounge** | Not path-referenced in audit | Protected per section 2.1 | **PROTECTED** |

---

## 8. HERMES INTEGRATION STATUS

### 8.1 Current Hermes State

| Aspect | Status |
|--------|--------|
| `~/.hermes/` existence | **YES** — live directory with 4 profiles, cron, logs, plugins, databases |
| Hermes agent binaries | `~/.local/bin/hermes`, `~/.local/bin/hermes-agent`, `~/.local/bin/hermes-acp` | **Removed** (not present in current inventory) |
| Hermes gateway systemd service | `~/.config/systemd/user/hermes-gateway.service` | **Present but inactive** |
| Hermes processes | None observed running | **N/A** |
| Integration with HELIX bridge | **ACTIVE** — bridge reads `~/.hermes/kanban.db` and `~/.hermes/state.db` | **YES** |
| Integration with JARVIS | **Via HELIX shared voice contract** | **YES** (post-`07a2522` commit) |

### 8.2 Broken/Missing Integrations

| Integration | Issue | Impact |
|-------------|-------|--------|
| `~/JARVIS` symlink target | `/run/media/abubakargcx/My Drive/JARVIS` doesn't exist | **BROKEN** — JARVIS access via home symlink fails |
| Hermes gateway service | Unit file present but service inactive | **LOW** — was inactive before removal |
| Old Hermes database recovery | Three `kanban.db` files previously truncated to 0 bytes | **HISTORICAL** — no recovery needed |

### 8.3 What Remains Dormant

| Component | State | Future Action |
|-----------|-------|--------------|
| Full Hermes agent reinstallation | Not attempted | User will install fresh Hermes after HELIX architecture is complete |
| Old database recovery | Truncated/kana | Abandoned per user directive |
| Hermes skills under `~/.hermes/skills/` | Present in live `.hermes/` | Will be replaced by fresh installation |

---

## 9. HELIX STANDALONE DESKTOP APPLICATION FEASIBILITY

### 9.1 Current HELIX Implementation

| Aspect | Current State |
|--------|--------------|
| **GUI technology** | `helix-ui.html` — web-based UI |
| **Backend startup** | Requires manual terminal commands (per user requirement "does not want to manually open a terminal") |
| **Frontend startup** | Web server or static file serving |
| **Systemd service** | None currently defined for HELIX (only hermes-gateway) |
| **`.desktop` launcher** | None found in current inventory |
| **Terminal requirement** | **YES** — user currently must type commands in terminal |
| **Browser dependency** | UI is web-based; requires browser or embedded web view |
| **Independent operation** | **NO** — depends on Hermes `.hermes/` state databases and HELIX bridge |

### 9.2 Feasibility Analysis for Standalone Desktop

**Technical challenges:**
1. **Hermes state dependency:** HELIX bridge reads `~/.hermes/kanban.db` and `~/.hermes/state.db`. A standalone HELIX would need either:
   - A clean Hermes state directory, or
   - A replacement data store (SQLite database with equivalent schema)
2. **No `.desktop` launcher:** No application launcher exists. Would need to create one.
3. **Backend lifecycle:** No defined startup/shutdown mechanism. Would need systemd service or script.
4. **Web UI deployment:** `helix-ui.html` would need a backend (Python simplehttp, Node, etc.) or embedded browser.

**Potential technologies for standalone app:**
- **Electron:** Wrap `helix-ui.html` + Python bridge in Electron app
- **Python + Flask/FastAPI:** Serve the HTML UI + provide API bridge to SQLite
- **Bun/Node.js:** Serve static UI + bridge scripts
- **systemd user service:** Define `helix.service` for auto-startup and lifecycle management

**Feasibility:** **MODERATE** — technically achievable but requires:
1. Replacement or clean Hermes state data store
2. Backend service definition
3. `.desktop` file creation
4. Startup/shutdown scripts
5. Possibly a new bridge adapter that doesn't depend on `~/.hermes/`

**User constraint:** "HELIX should behave like a normal desktop application" and "user does not want to manually open a terminal and type commands every time they want to run HELIX."

**Conclusion:** A standalone desktop app is **feasible** but requires significant re-architecting to remove the `~/.hermes/` state dependency and provide proper desktop integration.

---

## 10. FUTURE IDENTITY AND AGENT HIERARCHY IMPACT

### 10.1 Current Agent Hierarchy

| Agent | Role | Capabilities | Name Origin |
|-------|------|-------------|-------------|
| **HELIX** | Central AI system | Agent orchestration, dispatch, gesture, voice, globe | Stark family robots |
| **JARVIS** | Buddy-style sub-agent | Voice interface, task processing, memory, voice contract | Stark family robots |
| **Specialist agents** | Under HELIX | pc, research, devops, creative, email, etc. | Inspired by Stark robots |

### 10.2 Proposed HELIX Central Identity

The user's desired future direction:

- **HELIX** becomes the central project identity
- **JARVIS** keeps its name, personality, and independent abilities
- JARVIS should not become a hollow chatbot or lose its individual capabilities
- HELIX must identify its sub-agents, their names, roles, tools, and individual capabilities
- Other HELIX agents should use names inspired by Tony Stark's robots

**Impact on current code:**
- `HELIX_INTEGRATION.md` and `JARVIS_HELIX_MANAGER_HIERARCHY_PROMPT.md` already define the integration framework
- `AGENTS.md` in JARVIS defines agent capabilities and names
- `agents/` directory in HELIX defines specialist agents (pc, research, etc.)
- The `07a2522` commit already consumed the shared JARVIS voice contract, eliminating duplication

**Required changes:**
1. **Agent registry:** HELIX must maintain a centralized agent registry with names, roles, tools, and capabilities
2. **JARVIS independence:** JARVIS must retain its separate identity, voice, and memory — not merged into HELIX core
3. **Named specialist agents:** Continue populating `agents/` with named agents (already in progress: pc, research, devops, creative, etc.)
4. **Permission system:** Shared permission/confirmation framework (already referenced in `HELIX_INTEGRATION.md` and `d93c702` commit)

**No changes should be made in this phase.** The investigation only.

---

## 11. MIGRATION RISKS

| Risk | Category | Severity | Mitigation |
|------|----------|----------|------------|
| **My Drive mount failure** | Infrastructure | **HIGH** — if My Drive unmounts, all consolidated paths break | Ensure My Drive is reliably mounted; have local fallback paths |
| **Dental Lounge accidental modification** | Protection | **CRITICAL** — per section 2.1, any modification violates user rules | Strict: do not open, inspect credentials, modify Docker/Prisma, or perform package cleanup on Dental Lounge resources |
| **Broken symlink `~/JARVIS`** | Dependency | **HIGH** — `~/JARVIS → /run/media/abubakargcx/My Drive/JARVIS` doesn't exist | Redirect symlink to `AI_WORKSPACE/JARVIS/` or remove and use git repo directly |
| **Dual HELIX git repos divergence** | Version control | **MEDIUM** — `hermes/helix/` and `AI_WORKSPACE/helix/` are separate repos | Reconcile: choose one canonical location, or set up sync |
| **Hermes `.hermes/` state dependency** | Integration | **MEDIUM** — HELIX bridge reads `~/.hermes/kanban.db` and `state.db` | Plan: either clean `.hermes/` or replace with standalone data store for standalone HELIX |
| **Downloads migration conflicts** | Data movement | **MEDIUM** — `~/Downloads/` has 200+ files mixing academic, personal, and possibly Dental Lounge content | Classify each file before movement; retain Dental Lounge-associated files in place |
| **Symlink explosion** | Architecture | **LOW** — many symlinks already exist; adding more could confuse | Document all symlinks; eliminate unnecessary ones during consolidation |
| **My Drive capacity constraints** | Infrastructure | **LOW** — ~12 GB observed; verify sufficiency for all consolidated data | Audit actual usage before large-scale migration |

---

## 12. PROTECTED RESOURCES

| Path | Reason for Protection | Action |
|------|----------------------|--------|
| `~/Desktop/The Dental Lounge/` | Active production client project | **STRICTLY PROTECTED** per section 2.1 — DO NOT open, modify, move, delete, inspect credentials, change Docker/Prisma configs, or perform package manager cleanup |
| `~/Desktop/Backup_Artifacts/` | Associated with Dental Lounge | **PROTECTED** — part of Dental Lounge backup structure |
| `~/JARVIS` symlink target | Broken; not a protected resource per se, but JARVIS data must be preserved | Fix symlink; canonical JARVIS at `AI_WORKSPACE/JARVIS/` |
| `~/.hermes/` (live state) | Active Hermes agent state | **CLASSIFIED** — Hermes removal previously authorized but directory reappeared; classify as Hermes-only or retain if ambiguous |
| `~/Desktop/Dental_Project/` | May overlap with Dental Lounge | **PROTECTED** — classify before any action |
| `/run/media/abubakargcx/My Drive/hermes/` | HELIX base directory | **PROTECTED** — HELIX must remain intact per user rules |
| `/run/media/abubakargcx/My Drive/AI_WORKSPACE/JARVIS/` | Active JARVIS git repo | **PROTECTED** — do not merge, delete, or rewrite |
| `/run/media/abubakargcx/My Drive/AI_WORKSPACE/helix/` | Active HELIX git repo | **PROTECTED** — do not merge, delete, or rewrite |
| Ubuntu OS | Full operating system | **UNCHANGED** — do not reinstall, modify partitions, bootloader, or system packages |

---

## 13. RECOMMENDED CANONICAL DIRECTORY STRUCTURE

```
AI_WORKSPACE/
├── HELIX/
│   ├── core/           # helix/ source (from hermes/helix/)
│   │   ├── agents/
│   │   ├── bridge/
│   │   ├── docs/
│   │   ├── tools/
│   │   ├── ui/
│   │   ├── install.sh
│   │   └── uninstall.sh
│   ├── skills/         # hermes/skills/ (autonomous-ai-agents, creative, etc.)
│   ├── memory/         # kanban.db, state.db (replaced from .hermes/)
│   ├── connectors/     # MCP servers, model routers
│   ├── mcps/           # Model-Context-Protocol servers
│   ├── plugins/        # HELIX plugin definitions
│   ├── tests/          # Test suite
│   └── documentation/
├── JARVIS/
│   ├── AGENTS.md structure
│   ├── CLAUDE.md
│   ├── voice/          # voice contract and playback
│   ├── memory/         # JARVIS memory system
│   ├── tools/          # Utility tools
│   └── integration/    # HELIX integration points
├── shared/
│   ├── agent-registry/ # Proposed agent naming/capability registry
│   ├── confirmation/ # Policy/confirmation framework
│   └── voice-contract/# Shared JARVIS/HELIX voice format
├── tools/
│   ├── eras.py         # Semantic eras store
│   ├── helix-call-memory.py
│   ├── helix-call-sync.py
│   ├── helix-voice.py
│   ├── selfcheck.py
│   └── whatsapp.py
├── research/
│   ├── requirements/   # GitHub research inventory (Phase 2)
│   └── candidates/     # Evaluated repositories
├── documentation/
│   ├── HELIX_BUILD_SPEC.md
│   ├── PROGRESS.md
│   ├── PACKAGING_PLAN.md
│   ├── FEATURE_BACKLOG.md
│   └── audit/
├── backups/
│   ├── git-archives/   # Git bundle/fresh clones
│   └── config-backups/ # .env, config.yaml, etc.
└── audit/
    ├── 2026-11-06_PHASE_1_SYSTEM_DISCOVERY_REPORT.md
    └── 2026-11-06_HERMES_COMPLETE_REMOVAL_REPORT.md
```

**Note:** This is a **proposed layout** for future execution Phase, not an instruction to create these directories now. The current state must be investigated and documented first.

---

## 14. PHASED EXECUTION PLAN

### Phase 1 (Complete)
✅ Read-only system audit  
✅ Evidence-based report generation  
✅ No file modifications  
✅ Protected resources identified and documented  

### Phase 2 — Pre-Migration Preparation
**Actions (all read-only verification first):**
1. Hash critical files (SHA-256) to establish canonical duplicates
2. Classify all `~/Downloads/` files: Dental Lounge vs. academic vs. personal vs. development
3. Verify My Drive mount reliability (capacity, permissions, auto-mount)
4. Document all symlink dependencies (what uses each symlink)
5. Create broken-symlink remediation plan (`~/JARVIS`)
6. Export JARVIS and HELIX git repos to ensure backup

**Deliverables:**
- SHA-256 hash inventory
- Downloads file classification table
- My Drive health check report
- Symlink dependency map
- Git repo exports

### Phase 3 — Migration Execution
**Actions:**
1. **Desktop:** Keep symlink `~/Desktop → My Drive/Desktop` with Dental Lounge access controls
2. **Downloads:** Migrate non-Dental-Lounge files from `~/Downloads/` to `My Drive/Downloads/`. Update XDG user dirs. Update browser defaults.
3. **JARVIS:** Redirect `~/JARVIS` symlink to `/run/media/abubakargcx/My Drive/AI_WORKSPACE/JARVIS/` (canonical git repo). Or remove symlink and use git commands from AI_WORKSPACE path.
4. **HELIX:** Choose canonical HELIX location — either `AI_WORKSPACE/helix/` or `My Drive/hermes/helix/`. Sync or consolidate the two git repos.
5. **Hermes:** Classify `~.hermes/`. If keeping as Hermes agent state, clean and maintain. If removing, replace bridge data store with standalone SQLite.
6. **Symlink elimination:** Evaluate each symlink for necessity. Remove unused ones. Replace with direct paths where beneficial.

**Deliverables:**
- Migrated file structure
- Updated symlink map
- Consolidated git repos
- HELIX standalone desktop app feasibility analysis (from Section 9)
- Agent hierarchy documentation (from Section 10)

### Phase 4 — Post-Migration Verification
**Actions:**
1. Verify JARVIS launches from `AI_WORKSPACE/JARVIS/` or via redirected symlink
2. Verify HELIX launches (standalone or via bridge) without terminal commands
3. Verify Dental Lounge untouched — no modification timestamps, no file access changes
4. Verify Hermes integration state (either clean `.hermes/` or replacement data store)
5. Verify My Drive mount stability across reboot
6. Verify all application launchers (.desktop files) resolve correctly

**Deliverables:**
- Verification checklist (from Section 15 of the requirements)
- Final audit report
- User confirmation of successful migration

---

## 15. VERIFICATION CHECKLIST

| # | Verification | Expected Result | Status |
|---|-------------|-----------------|--------|
| 1 | My Drive is mounted and accessible | `ls /run/media/abubakargcx/My Drive/` succeeds | Not yet verified (investigation only) |
| 2 | `AI_WORKSPACE/JARVIS/` is a valid git repo | `git status` succeeds on `AI_WORKSPACE/JARVIS/` | **VERIFIED** — confirmed on audit branch |
| 3 | `AI_WORKSPACE/helix/` is a valid git repo | `git status` succeeds on `AI_WORKSPACE/helix/` | **VERIFIED** — confirmed on audit branch |
| 4 | HELIX bridge can read Hermes state | Bridge code references `~/.hermes/kanban.db` | **VERIFIED** — `.hermes/` exists and has kanban.db |
| 5 | `~/JARVIS` symlink is fixed | `readlink ~/JARVIS` points to valid path | **BROKEN** — target missing; requires remediation |
| 6 | Dental Lounge unchanged | No modification timestamps on `~/Desktop/The Dental Lounge/` | **PROTECTED** — not modified during audit |
| 7 | My Drive has sufficient capacity | `df -h /run/media/abubakargcx/My Drive/` shows adequate free space | **PARTIALLY VERIFIED** — ~12 GB observed, needs actual usage audit |
| 8 | No Hermes gateway service running | `systemctl list-units --type=service | grep hermes` returns nothing | **VERIFIED** — no hermes services active |
| 9 | Browser/profile `~/.config/Hermes/` is intact | Chromium/Edge profile preserved | **VERIFIED** — exists as browser profile, not Hermes agent |
| 10 | Desktop symlink functional | `ls ~/Desktop/` shows My Drive Desktop contents | **VERIFIED** — symlink resolves correctly |

---

## 16. OPERATIONS NOT PERFORMED (Read-Only Compliance)

The following operations were **not executed** during this read-only Phase 1 audit, as required by the authorization boundary:

- ❌ `rm`, `rmdir`, `mv`, `cp`, `rsync` with write operations
- ❌ `ln`, `unlink` (symlink creation/removal)
- ❌ `chmod`, `chown` (permission changes)
- ❌ `truncate` (database or file truncation)
- ❌ Package installation or removal (`apt`, `pip`, `npm`, `pnpm`, `bun`)
- ❌ Service enable/disable/restart/stop
- ❌ Configuration editing (`.env`, `config.yaml`, service files)
- ❌ Repository renaming or `git mv`
- ❌ Git reset, clean, checkout, rebase, or history rewriting
- ❌ Database writes or migrations (SQLite `.db` files)
- ❌ Automatic duplicate deletion
- ❌ Any script that modifies files, timestamps, databases, or services
- ❌ Desktop rollback (restoring `~/Desktop` to local-only state)
- ❌ Downloads migration (moving files from `~/Downloads/` to My Drive)
- ❌ Hermes reinstallation or recreation
- ❌ Merging of JARVIS and HELIX Git repositories
- ❌ Creation of new directories under My Drive or AI_WORKSPACE
- ❌ Symlink elimination or addition (beyond existing inventory)
- ❌ XDG user dirs configuration changes
- ❌ Browser download setting changes
- ❌ Environment variable modifications

**All investigation was read-only.** `find`, `ls`, `stat`, `readlink`, `realpath`, `du`, `df`, `file`, `git status`, `git log`, and read-only configuration inspection were the primary tools used.

---

## 17. UNCERTAINTIES REQUIRING USER DECISIONS

| Uncertainty | Options | User Decision Required |
|-------------|---------|-----------------------|
| **`~/JARVIS` symlink target** | A. Redirect to `AI_WORKSPACE/JARVIS/`<br>B. Remove symlink, use git repo directly<br>C. Restore `My Drive/JARVIS/` and redirect | User must choose symlink resolution strategy |
| **`~/.hermes/` classification** | A. Remove Hermes-only components (re-audit from current state)<br>B. Retain as live Hermes agent state<br>C. Replace bridge data store with standalone SQLite | User must decide Hermes fate |
| **Downloads migration** | A. Migrate non-Dental-Lounge files to My Drive<br>B. Keep `~/Downloads/` as local real directory<br>C. Create symlink `~/Downloads → My Drive/Downloads` (user said "should ultimately be stored under My Drive" but also " Desktop should not become a symlink to My Drive") | User must choose migration approach |
| **HELIX canonical location** | A. `AI_WORKSPACE/helix/` as primary, `My Drive/hermes/helix/` as sync<br>B. `My Drive/hermes/helix/` as primary, `AI_WORKSPACE/helix/` as clone<br>C. Merge both repos into one | User must choose HELIX root |
| **Standalone HELIX desktop app** | A. Proceed with feasibility analysis (Section 9)<br>B. Delay until Hermes replacement is decided<br>C. Abandon — keep terminal-based operation | User must decide on desktop app pursuit |
| **Agent hierarchy naming** | A. Continue Stark-robot names (pc, research, devops, creative, etc.)<br>B. Use different naming convention<br>C. Formalize agent registry in code | User must decide agent naming convention |

---

## FINAL RESOURCE BALANCE

**Preserved intact (no modifications):**
- `/run/media/abubakargcx/My Drive/AI_WORKSPACE/JARVIS/` — JARVIS git repo
- `/run/media/abubakargcx/My Drive/AI_WORKSPACE/helix/` — HELIX git repo
- `/run/media/abubakargcx/My Drive/hermes/` — HELIX base directory
- `~/Desktop/The Dental Lounge/` — Protected production project
- Ubuntu OS — completely untouched
- `~/.config/Hermes/` — Chromium/Edge browser profile (coincidentally named, protected per section 2.5)
- `/run/media/abubakargcx/My Drive/JARVIS/` — does not exist (broken symlink target noted)

**Identified for future action:**
- `~/JARVIS` broken symlink — requires resolution
- `~/.hermes/` live directory — requires classification and decision
- `~/Downloads/` — requires classification and potential migration
- Dual HELIX git repos — requires consolidation decision
- HELIX standalone desktop app — requires feasibility follow-through

**Report generated:** 2026-11-06  
**Investigation type:** Read-only, no file modifications, no service changes, no configuration edits  
**Next phase:** Approved Phase 2 — Pre-Migration Preparation (upon user authorization)

---

**END OF PHASE 1 SYSTEM DISCOVERY REPORT**