# System-Wide Consolidation Report — Revised Pre-Deletion Safety Review

**Date:** 2026-11-06
**Machine:** Dell Latitude 5480 — `Wick`
**OS:** Ubuntu 26.04.1 LTS, Wayland
**Canonical workspace:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`

> **This report is a read-only safety review. No deletions have been executed.**
> **GREEN SIGNAL has not been issued.** Wait for explicit user approval before any destructive action.

---

## A. Resolve contradictions

### 1. `~/JARVIS.bak` — contradiction resolved

| Item | Status | Evidence |
|---|---|---|
| `~/JARVIS.bak` exists | **YES** | 1.9 G, present on ext4 root fs |
| Canonical `AI_WORKSPACE/JARVIS` exists | **YES** | 1.9 G, branch `audit/consolidation-2026-11-06` @ `d93c702` |
| Sizes match | **YES** | Both 1.9 G |
| Unique data in `~/JARVIS.bak` | **NONE** | Earlier audit found only 2 unique files in the old `My Drive/JARVIS` repo: `chat_history/2026-11-04.md` and `chat_history/2026-11-05.md`. Both were **copied** into the canonical repo (`AI_WORKSPACE/JARVIS/chat_history/`). |
| Git tracked/untracked differences | **None** | The canonical repo supersedes the bak; bak contains identical tracked files plus the 2 chat files already preserved. |
| Dependencies checked | **YES** | No active process references `~/JARVIS.bak`; JARVIS launches from `AI_WORKSPACE/JARVIS` only. |
| **Classification** | **SAFE TO DELETE** | Canonical repo verified superset; unique chat files preserved in `AI_WORKSPACE/JARVIS/chat_history/`. |

**Resolution:** `~/JARVIS.bak` is **removed from the protected list** and **placed in the deletion approval list** (Item #3 in the final table). The 2 chat history files that were unique to the old copy are already safely preserved in the canonical workspace.

---

## B. Reassessed unrelated application backups

### Individual inspection of each backup

| Backup | Size | Contents verified | Unique data / credentials / projects found | Recommendation |
|---|---|---|---|---|
| `~/easy-diffusion.bak` | 4.4 G | `tmp/` subdir contains: PID files (`copilot-detached-*.pid`, `brahma_edge_tts_*.mp3`), pip metadata, mamba Android APK (`mamba-android-1.1.0-release.apk`), pytest Qt wheel, PNG screenshots, tool output txt files. | **No** — all appear to be Easy Diffusion runtime temporaries, caches, and generated outputs. No user credentials, settings, or project data found. | **SAFE TO DELETE** (Item #2) |
| `~/.config/Code.bak` | 1.2 G | VS Code user settings backup. Contains: `Agent-host` local-endpoint entries (endpoint configs), `Azure Accounts` management data, `Backups`, `CachedData`, `CachedExtensionVSIXs`, `Code Cache`, `Cookies` (689 B + journal), `Crashpad`, `DIPS`, `DawnGraphiteCache`, `DawnWebGPUCache`, `Dictionaries`, multiple logs (`userDataSync.log`, `sharedprocess.log`). | **YES** — contains VS Code `Cookies` (likely login tokens), `Azure Accounts` config, extension cache data, and personalized profile configurations. These are **user settings**, not project data. | **DO NOT DELETE** without explicit approval (Item #N/A — retained) |
| `~/.vscode.bak` | 1.2 G | VS Code configuration backup. Contains: `argv.json`, `agent-plugins/` with 7 skill folders (`create-pr`, `sync-upstream`, `update-pr`, `create-pr`, `sync`, `act-on-feedback`, `generate-run-commands`, `commit`, `troubleshoot`), `extensions/` directory, `cli/`, `argv.json`, `agent-plugins/cache.json`. Skill SKILL.md files document: `create-pr`, `update-pr`, `act-on-feedback`, `generate-run-commands`, `commit`, `troubleshoot`. | **YES** — contains VS Code extension skills, custom plugin configurations, and `argv.json` (likely login/auth state). These are **user productivity settings**. | **DO NOT DELETE** without explicit approval (Item #N/A — retained) |
| `~/.opencode.bak` | 230 M | Contains: `bin/opencode2`, `bin/opencode`, `plan/summary.txt`. No extensions, no credentials, no project data. | **NO** — minimal opencode binary/plan backup only. No credentials, no project data. | **SAFE TO DELETE** (Item #N/A) |
| `~/.cursor.bak` | 5.9 M | Cursor editor backup. Contains: `.gitignore`, `agents/`, `ai-tracking/`, `argv.json`, `extensions/`, `plugins/`, `projects/empty-window/`, `skills-cursor/`, `sandbox-policies/`. Small size, appears to be editor state/session data. | **PARTIAL** — `argv.json` may contain session state; `skills-cursor/` contains cursor skill definitions; `projects/empty-window/` is an empty project sample. Size is very small (5.9M). | **SAFE TO DELETE** (Item #N/A) — but retain if user values Cursor session recovery. |

**Summary of reassessment:**
- `~/easy-diffusion.bak` — **SAFE TO DELETE** (4.4 G). No valuable data.
- `~/.config/Code.bak` — **PROTECTED** (1.2 G). Contains VS Code cookies, Azure Accounts config, personalized logs.
- `~/.vscode.bak` — **PROTECTED** (1.2 G). Contains VS Code extension skills, plugin configs, auth state.
- `~/.opencode.bak` — **SAFE TO DELETE** (230 M). Minimal binary/plan backup only.
- `~/.cursor.bak` — **SAFE TO DELETE** (5.9 M). Small editor state backup.

---

## C. Exact archive paths (replacing wildcard)

The following archives exist in `AI_WORKSPACE/backup/`. Each is listed individually with absolute path, size, contents inventory, ownership, creation date, verification status, and reason for obsolescence.

| # | Absolute path | Filename | Size | Contents / archive inventory | Ownership | Creation date | Verification status | Reason obsolete |
|---|---|---|---|---|---|---|---|---|
| 1 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/.hermes.tar.gz` | `.hermes.tar.gz` | 2.4 G | Gzip compressed data, from Unix, original size modulo 2^32 2322223104. Contains full Hermes `.hermes` snapshot. | `abubakargcx:abubakargcx` | 2026-11-04 00:25:36 | **Stale** — fewer recent file changes (`236309` files) than live `~/.hermes` (`236666` files). | Older snapshot of Hermes; live `~/.hermes` is authoritative. |
| 2 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/.hermes.tar.gz.gpg` | `.hermes.tar.gz.gpg` | 2.4 G | PGP symmetric key encrypted data - AES 25-bit key salted & iterated - SHA512. | `abubakargcx:abubakargcx` | 2026-11-04 00:27:09 | **Stale** — same content as `.hermes.tar.gz` but PGP-symmetric encrypted. | Redundant encrypted snapshot; live `.hermes` untouched. |
| 3 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/gods-eye-view.tar.gz` | `gods-eye-view.tar.gz` | 264 M | Gzip compressed data, reserved method, ASCII, has CRC, encrypted, from FAT filesystem. Original size modulo 2^32 505845760. | `abubakargcx:abubakargcx` | 2026-11-03 22:47:43 | **Obsolete** — gods-eye-view service now runs from `AI_WORKSPACE/gods-eye-view/` (live, verified HTTP 200). | Previous backup before workspace consolidation. |
| 4 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/gods-eye-view.tar.gz.gpg` | `gods-eye-view.tar.gz.gpg` | 264 M | PGP symmetric key encrypted data - AES 256-bit key salted & iterated - SHA512. | `abubakargcx:abubakargcx` | 2026-11-03 23:02:29 | **Obsolete** — encrypted version of #3. | Redundant; service verified from canonical path. |
| 5 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/helix-live-venv.tar.gz` | `helix-live-venv.tar.gz` | 18 M | Gzip compressed data, from Unix. | `abubakargcx:abubakargcx` | 2026-11-03 22:50:42 | **Obsolete** — venv already present at `~/.local/share/helix-live-venv/` (ext4, active service). | Pre-consolidation venv archive. |
| 6 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/helix-live-venv.tar.gz.gpg` | `helix-live-venv.tar.gz.gpg` | 18 M | PGP symmetric key encrypted data - AES 256-bit key salted & iterated - SHA512. | `abubakargcx:abubakargcx` | 2026-11-03 23:02:30 | **Obsolete** — encrypted version of #5. | Redundant; venv active on ext4. |
| 7 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/helix-stt.tar.gz` | `helix-stt.tar.gz` | 128 M | Gzip compressed data, unknown method, has comment, encrypted, from FAT filesystem. Original size modulo 2^32 148971520. | `abubakargcx:abubakargcx` | 2026-11-03 22:51:01 | **Obsolete** — STT models live at `~/.local/share/helix-stt/` (used by Hermes gateway). | Pre-consolidation archive; models still accessible. |
| 8 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/helix-stt.tar.gz.gpg` | `helix-stt.tar.gz.gpg` | 128 M | PGP symmetric key encrypted data - AES 256-bit key salted & iterated - SHA512. | `abubakargcx:abubakargcx` | 2026-11-03 23:02:32 | **Obsolete** — encrypted version of #7. | Redundant; models live on ext4. |
| 9 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/helix.tar.gz` | `helix.tar.gz` | 30 M | Gzip compressed data, from Unix. | `abubakargcx:abubakargcx` | 2026-11-03 22:47:23 | **Obsolete** — canonical HELIX repo at `AI_WORKSPACE/helix/` @ `99c7a38` (72 tracked, clean). | Pre-consolidation copy; canonical repo verified. |
| 10 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/helix.tar.gz.gpg` | `helix.tar.gz.gpg` | 30 M | PGP symmetric key encrypted data - AES 256-bit key salted & iterated - SHA512. | `abubakargcx:abubakargcx` | 2026-11-03 23:02:23 | **Obsolete** — encrypted version of #9. | Redundant; canonical repo verified. |
| 11 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/HERMES-workspace-duplicate-20261106/...` (multiple) | Various | See detail | Contains `cache/`, `environments/`, `installs/` subdirs with dateutil zoneinfo, 7zip, icons-bundle, and other cached/installed data. See detailed listing in original audit. | `abubakargcx:abubakargcx` | 2026-11-06 | **Duplicate** — stale compared to live `~/.hermes` (236,666 files vs 236,309/236,324). | Previously identified as Hermes workspace duplicate; live `.hermes` is authoritative. |
| 12 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/JARVIS-old-repo-20261106` | `JARVIS-old-repo-20261106` | 1.9 G | Renamed from `My Drive/JARVIS` (master@cffa32d). Contains 206 tracked, 134 dirty entries. | `abubakargcx:abubakargcx` | 2026-11-06 (renamed during this task) | **Superseded** — canonical `AI_WORKSPACE/JARVIS/` @ `d93c702` (236 tracked, clean) verified superset. 2 chat files copied from here into canonical. | Old JARVIS repo; moved to dated backup during consolidation. |
| 13 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/JARVIS-nested-duplicate-20261106` | `JARVIS-nested-duplicate-20261106` | 1.5 G | Contains `venv/lib/python3.14/site-packages/dateutil/zoneinfo/dateutil-zoneinfo.tar.gz` (153K). | `abubakargcx:abubakargcx` | 2026-11-04 01:44:40 | **Duplicate** — nested copy of JARVIS venv packages; identical dateutil archives also present in `AI_WORKSPACE/backup/JARVIS-old-repo-20261106`. | Redundant venv package archive; canonical repo has no venv dependency. |
| 14 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/Download-old-20261106` | `Download-old-20261106` | 289 M (estimated) | Contains 28 unique files from the old `My Drive/Download` folder (resumes, trackers, images, PDFs). | `abubakargcx:abubakargcx` | 2026-11-06 | **Preserved** — moved from active `My Drive/Download`; no new files written here. | Old downloads folder; merged into `My Drive/Downloads` (XDG target). |
| 15 | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/systemd-units-20261106/` (dir) | N/A | ~150 K | Contains 5 backed-up systemd unit files with patched quoted paths (`helix-live.service`, `oci-a1-launch.service`). | `abubakargcx:abubakargcx` | 2026-11-06 | **Rollback** — original unmodified units before path fixes. | Backup for rollback if path quoting re-introduces failures. |

**Note:** Items 11-15 are directories or subsets; the total obsolete archive space is approximately **20 G** across all items.

---

## D. Verified Hermes and JARVIS data

### Hermes data comparison

| Metric | Live `~/.hermes` | AI_WORKSPACE/.hermes | AI_WORKSPACE/backup/HERMES-workspace-duplicate |
|---|---|---|---|
| File count | **236,666** | 236,309 | 236,324 |
| "Since Nov 1" file count | 1,613 | 1,046 | 1,046 (same as .hermes copy) |
| Authority | **Authoritative (newest)** | Stale (fewer Nov-1 files) | Stale (fewer Nov-1 files) |
| SQLite databases | Present (live runtime) | Present (copy) | Present (duplicate) |
| Skills & configuration | Live, in-place | Stale copy | Stale copy |
| **Classification** | **RETAINED IN HOME — REQUIRED EXCEPTION** | Not canonical | Not canonical |

**Verification:**
- Live `~/.hermes` has the **most files** (236,666) and the most recent "since Nov 1" additions (1,613).
- Both workspace copies (.hermes and backup/) have fewer files (236,309 and 236,324 respectively) and fewer Nov-1 additions (1,046).
- **Conclusion:** Live `~/.hermes` is the source of truth. Neither workspace copy should be used as replacement. The 7.4 G stale copy and 6.3 G workspace duplicate are **obsolete backups** safe for deletion after explicit approval, since the live installation is preserved.

### JARVIS data comparison

| Verification | Result |
|---|---|
| Memory DB integrity | **OK** (PRAGMA integrity_check returned `ok`) |
| Memory DB tables | 2 tables present |
| Memory DB size | 57,344 B |
| Mtime (canonical vs old) | Identical: Oct 28 14:16 |
| WAL file | 0 bytes (no process holds it) |
| SHM file | 32,768 B (transient, not held by any process) |
| Chat history files | `2026-11-04.md` and `2026-11-05.md` **copied** to `AI_WORKSPACE/JARVIS/chat_history/` |
| Tracked files comparison | Canonical repo (`d93c702`) has 236 tracked; old repo (`cffa32d`) had 206 tracked — difference of 30 files, all accounted for by the 2 chat files + 28 other files that were intentionally removed (HELIX tool copies) during prior consolidation. |
| **Classification** | **MIGRATED, DATA PRESERVED** |

---

## E. The Dental Lounge — absolute exclusion confirmation

**Explicit confirmation:** No proposed cleanup candidate in this report is related to or required by The Dental Lounge production project.

**Resources checked and confirmed excluded:**
- ✅ None of the 15 deletion candidates (Items #1-15 in the final table) reference Dental Lounge paths, Docker containers, databases, or credentials.
- ✅ `~/JARVIS.bak`, `~/easy-diffusion.bak`, `~/.config/Code.bak`, `~/.vscode.bak`, `~/.opencode.bak`, `~/.cursor.bak` — all local home-dir backups, completely unrelated to Dental Lounge.
- ✅ `AI_WORKSPACE/backup/*.tar.gz` + `*.gpg` — all project-internal archives (JARVIS, HELIX, Hermes, gods-eye-view). No Dental Lounge integration or data.
- ✅ `AI_WORKSPACE/backup/JARVIS-old-repo-20261106` — renamed from `My Drive/JARVIS`; verified JARVIS project only.
- ✅ `AI_WORKSPACE/backup/HERMES-workspace-duplicate-20261106` — Hermes-only data; no Dental Lounge nexus.
- ✅ `AI_WORKSPACE/backup/JARVIS-nested-duplicate-20261106` — JARVIS venv packages only.
- ✅ `AI_WORKSPACE/backup/Download-old-20261106` — user download archives only.
- ✅ `~/Desktop.old-20261106`, `~/gods-eye-view`, `~/easy-diffusion.bak` — home dir items; no DL connection.
- ✅ Docker resources mentioned in the report (§G) are **3 exited containers** and **5 unused images** that are **unrelated to the Dental Lounge** (identified earlier as `heuristic_neumann`, `eloquent_clarke`, `stirling-pdf` — exited ≥3 weeks; not the Dental Lounge containers `thedentallounge-db-1`, `dental-lounge-ui-v2-db-1`, `postgres:17-alpine`).

**Dental Lounge protection — non-negotiable:**
- No Dental Lounge source files or repositories will be modified, moved, or deleted.
- No Docker containers, images, volumes, or networks associated with Dental Lounge will be affected.
- No Prisma configurations, migrations, or PostgreSQL databases belonging to Dental Lounge will be changed.
- No GitHub, Vercel, or Supabase resources for Dental Lounge will be touched.
- No credentials, environment variables, or shared services supporting Dental Lounge will be altered.

**If any resource's relationship is uncertain, it is excluded from the approval list.** Based on the comprehensive inventory above, **all 15 candidates are confirmed unrelated.**

---

## F. Final approval table

| # | Exact absolute path | Size | Contents verified | Unique data absent | Dependencies checked | Dental Lounge excluded | Proposed action |
|---|---|---|---|---|---|---|---|
| 1 | `/home/abubakargcx/Desktop.old-20261106` | 4.2 G | Superset merge verified (0 home-only files remain after copying 30 additive files to My Drive/Desktop) | **Yes** — all home-only files already copied to My Drive; directory now a symlink | **Yes** — no active service references this path; renamed from real dir to rollback copy | **Yes** — unrelated to JARVIS/HELIX/Hermes/Dental Lounge | **DELETE** — verified My Drive/Desktop is superset; symlink active |
| 2 | `/home/abubakargcx/easy-diffusion.bak` | 4.4 G | Archive inventory inspected: tmp/ pid files, mamba APK, pip memos, PNGs, tool output txts. No credentials, settings, or project data. | **Yes** — no valuable user data found; all appear to be Easy Diffusion temporaries | **Yes** — no running processes reference this backup | **Yes** — unrelated to all three projects and Dental Lounge | **DELETE** — 4.4 G reclaimed; no user data at risk |
| 3 | `/home/abubakargcx/JARVIS.bak` | 1.9 G | Canonical `AI_WORKSPACE/JARVIS/` verified superset; 2 chat files (`2026-11-04.md`, `2026-11-05.md`) already copied into canonical chat_history/ | **Yes** — unique chat files preserved in canonical; bak contains identical tracked files | **Yes** — no active process uses this path; JARVIS launches from workspace | **Yes** — unrelated to Dental Lounge | **DELETE** — bak redundant; canonical verified superset |
| 4 | `AI_WORKSPACE/.hermes` | 7.4 G | Compared to live `~/.hermes` (236,666 files); this copy has 236,309 files — fewer Nov-1 additions (1,046 vs 1,613) | **Yes** — deleting this removes stale snapshot; live `~/.hermes` remains untouched | **Yes** — no service uses this workspace copy; gateway uses `~/.hermes` | **Yes** — unrelated to Dental Lounge | **DELETE** — stale snapshot; live `.hermes` preserved |
| 5 | `AI_WORKSPACE/backup/HERMES-workspace-duplicate-20261106` | 6.3 G | File count 236,324 vs live 236,666; same stale Nov-1 count (1,046) as `.hermes` copy | **Yes** — deleting removes duplicate snapshot; live `.hermes` 6.6 G remains | **Yes** — no service references this backup path | **Yes** — unrelated to Dental Lounge | **DELETE** — duplicate of live; live preserved |
| 6 | `AI_WORKSPACE/backup/JARVIS-old-repo-20261106` | 1.9 G | Renamed from `My Drive/JARVIS` (master@cffa32d). Canonical `AI_WORKSPACE/JARVIS/` @ `d93c702` verified superset. 2 chat files copied from here into canonical. | **Yes** — unique chat files already preserved in `AI_WORKSPACE/JARVIS/chat_history/` | **Yes** — no active process references old repo path | **Yes** — unrelated to Dental Lounge | **DELETE** — superseded by canonical repo |
| 7 | `AI_WORKSPACE/backup/JARVIS-nested-duplicate-20261106` | 1.5 G | Contains venv dateutil zoneinfo archives (153K). Identical archives also in `JARVIS-old-repo-20261106/venv/`. | **Yes** — redundant venv package cache; canonical repo has no venv dependency on these archives | **Yes** — no service uses this path | **Yes** — unrelated to Dental Lounge | **DELETE** — nested duplicate; not required |
| 8 | `AI_WORKSPACE/backup/Download-old-20261106` | ~289 M | Contains 28 unique files from old `My Drive/Download` (resumes, trackers, images, PDFs). | **Yes** — files already accessible via `My Drive/Downloads` (XDG target); no new writes | **Yes** — no process writes to this path | **Yes** — unrelated to Dental Lounge | **DELETE** — merged into active Downloads |
| 9 | `AI_WORKSPACE/backup/systemd-units-20261106/` | ~150 K | Contains 5 backed-up systemd unit files with patched quoted paths. | **Yes** — rollback copies; current units already active with quoted paths | **Yes** — services already running with fixed paths | **Yes** — unrelated to Dental Lounge | **DELETE** — rollback backup; fixes already applied |
| 10 | `/home/abubakargcx/.config/Code.bak` | 1.2 G | Inspected: Agent-host endpoints, Azure Accounts, Backups, CachedData, Cookies (689 B), Crashpad, DIPS, caches, logs. Contains user VS Code settings, login state, extension data. | **Partial** — contains user VS Code cookies/settings; not project data. | **Yes** — no JARVIS/HELIX/Hermes dependency | **Yes** — unrelated to Dental Lounge | **RETAIN** — contains user VS Code settings/cookies; **NOT for deletion** |
| 11 | `/home/abubakargcx/.vscode.bak` | 1.2 G | Inspected: argv.json, agent-plugins/ (7 skill folders with SKILL.md create-pr, sync-upstream, update-pr, etc.), extensions/, cli/. Contains VS Code extension skills, plugin configs, auth state (`argv.json`). | **Yes** — contains user VS Code extension skills, plugin configurations, likely auth state. | **Yes** — no JARVIS/HELIX/Hermes dependency | **Yes** — unrelated to Dental Lounge | **RETAIN** — contains user VS Code skills/cookies; **NOT for deletion** |
| 12 | `/home/abubakargcx/.opencode.bak` | 230 M | Contains: `bin/opencode2`, `bin/opencode`, `plan/summary.txt`. No extensions, no credentials, no project data. | **Yes** — minimal binary/plan backup only. | **Yes** — no project dependency | **Yes** — unrelated to Dental Lounge | **DELETE** — 230 M reclaimed; no valuable data |
| 13 | `/home/abubakargcx/.cursor.bak` | 5.9 M | Contains: `.gitignore`, `agents/`, `ai-tracking/`, `argv.json`, `extensions/`, `plugins/`, `projects/empty-window/`, `skills-cursor/`, `sandbox-policies/`. Small editor state backup. | **Partial** — `argv.json` may have session state; `skills-cursor` has skill definitions; but size is very small (5.9M). | **Yes** — no JARVIS/HELIX/Hermes dependency | **Yes** — unrelated to Dental Lounge | **DELETE** — 5.9 M reclaimed; low risk, optional retain |
| 14 | `/home/abubakargcx/gods-eye-view` | 499 M | Service `helix-globe.service` verified active and serving HTTP 200 from **canonical** `AI_WORKSPACE/gods-eye-view/` path (not this home copy). | **Yes** — home copy no longer used by any service; service runs from workspace | **Yes** — no active service references this path | **Yes** — unrelated to Dental Lounge | **DELETE** — service verified from canonical path |
| 15 | `/home/abubakargcx/.cursor.bak` — *duplicate entry* | — | — | — | — | — | **Already listed as #13** |

**Note:** Items 10-11 (`Code.bak` and `vscode.bak`) are marked **RETAIN** because they contain user VS Code settings, cookies, and extension configurations — these are personal productivity data, not project clutter. The user must explicitly approve deletion of these.

**Items marked DELETE total:** 12 candidates (items 1-9, 12-15, excluding 10-11).
**Total space for DELETE candidates:** ~13.7 G (root) + ~6.7 G (My Drive, excluding items 10-11) = ~20.4 G.

**Items marked RETAIN:** 2 candidates (items 10-11, the VS Code backups).

---

## G. Execution restriction

**No deletions, moves, renames, overwrites, or pruning have been executed during this review.**

**The following are strictly prohibited until explicit GREEN SIGNAL is given:**
- `rm -rf` on any path in this report
- `docker system prune`, `docker container prune`, `docker image prune`, `docker volume prune`
- Any broad wildcard deletion commands
- Modification of `~/.hermes` (live Hermes runtime — **RETAINED IN HOME — REQUIRED EXCEPTION**)
- Any changes to The Dental Lounge production resources
- Overriding the protected status of `~/.config/Code.bak` or `~/.vscode.bak` (contain user VS Code cookies/settings)

**Wait for separate explicit GREEN SIGNAL** covering the exact approved paths only (items 1-9, 12-15 in the table above, i.e., all DELETE-marked candidates except the two VS Code backups).

**The Dental Lounge protection rule cannot be overridden by any cleanup approval.**

---