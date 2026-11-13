# AI_WORKSPACE Inventory

Snapshot taken 2026-11-06 at `/run/media/abubakargcx/My Drive/AI_WORKSPACE`, after the
consolidation described in `CLEANUP_PLAN.md`. Every number here was measured on disk,
not estimated.

---

## 1. Top level

| Path | Size | Kind | Status |
|---|---|---|---|
| `JARVIS/` | 1.9 G | Git repo (`audit/consolidation-2026-11-06` @ `6ba652b`) | Primary assistant. Authoritative. |
| `helix/` | 102 M | Git repo (`audit/consolidation-2026-11-06` @ `99c7a38`) | Orchestrator + globe UI. Independent history. |
| `gods-eye-view/` | 504 M | Git repo (`main` @ `0dbde1e`) | Upstream God's Eye View. Consumed by HELIX's globe service. |
| `backup/` | 15 G | No repo | Recovery store: tarballs + two relocated duplicate trees. |
| `DATA/` | 8.9 M | Data | Shared runtime data. No VCS. |
| `LMS Docs/` | 320 K | Research | NUML LMS2 evidence (6 files). |
| `JARVIS_LMS2_TECHNICAL_INVESTIGATION.md` | 96 K | Document | Prior read-only LMS audit. |
| `manifest_post_copy.sha256` | 68 B | Manifest | Copy-integrity record. |
| `.hermes/` | 6.3 G+ | Git repo inside (`hermes-agent` @ `bf0203a794`) | Hermes install. Live gateway reads `~/.hermes`. |
| `.local/` | — | Data | User-level runtime state. |
| `.freebuff/` | — | Tool state | Not project content. |
| `audit/` | new | Documents | This audit set. |

`HERMES/` (6.3 G) and `JARVIS/JARVIS/` (1.5 G) no longer exist at the top level: both were
relocated under `backup/` on 2026-11-06. See `REPOSITORY_STRUCTURE_REPORT.md`.

## 2. Git repositories

| Root | Branch | Commit | Tracked | Dirty | Remote | Verdict |
|---|---|---|---|---|---|---|
| `JARVIS/` | `audit/consolidation-2026-11-06` | `6ba652b` | 252 | 0 | **none configured** | Keep, authoritative |
| `helix/` | `audit/consolidation-2026-11-06` | `99c7a38` | 72 | 0 | `github.com/abubakar40-dev/helix.git` | Keep, independent |
| `gods-eye-view/` | `main` | `0dbde1e` | 1,292 | 4 | `github.com/bilawalsidhu/gods-eye-view.git` | Keep as upstream dependency |
| `.hermes/hermes-agent` | detached | `bf0203a794` | 20,799 | 0 | `github.com/NousResearch/hermes-agent.git` | Keep as third-party runtime |

`JARVIS/` has **no remote configured** — it has never been pushed, which satisfies the
no-push constraint by construction.

Nested `.git` directories found: `JARVIS/.git`, `helix/.git`, `gods-eye-view/.git`. No
repository-inside-repository remains outside `backup/`.

## 3. Code volume

| Project | Python files | Python lines | Non-Python source |
|---|---|---|---|
| JARVIS | 112 | 44,940 | UI assets, JS bridge, `venv/` (~3.1 G) excluded |
| helix | 18 | 5,511 | `ui/` Vite app (three.js globe), docs |
| gods-eye-view | 0 | 0 | 849 JS/HTML source files |

`JARVIS/venv/` (Python 3.14.4) is why the repo directory is 1.9 G while its source is
~45 k lines. It is not tracked.

## 4. Package managers and manifests

| Manifest | Project | Pinning |
|---|---|---|
| `JARVIS/requirements.txt`, `requirements-linux.txt` | JARVIS | **unpinned** — a reproducibility risk |
| `helix/pyproject.toml` (or `requirements.txt`) | helix | partially pinned |
| `helix/ui/package.json` + `package-lock.json` | globe UI | pinned by lockfile |
| `JARVIS/venv/` | JARVIS | Python 3.14.4 |

`python-kasa` was removed from both JARVIS requirement files (last consumer, smart-home,
was removed). No other dependency became orphaned by the cleanup: `brahma_connect` and
`smart_home` used only the standard library plus `requests`/`cryptography`, which other
modules still need.

## 5. Configuration, secrets, data stores

| Path | Contents | Handling |
|---|---|---|
| `JARVIS/config/api_keys.json` | Provider keys | Untracked. **Not** printed anywhere in this audit. |
| `JARVIS/config/app_settings.json` | App settings | Untracked. |
| `JARVIS/memory/personal_memory.sqlite3` | Personal memory | **Tracked in git** (pre-existing). See SECURITY S-6. |
| `JARVIS/chat_history/` | Conversation history | Untracked data. |
| `JARVIS/config/brahma_connect/` | Paired-device records | Moved to `backup/removed-20261106/config-brahma_connect`. |
| `JARVIS/config/smart_home.sqlite3`, `smart_home.key` | Smart-home device store + key | Moved to `backup/removed-20261106/`. |
| `~/.hermes/.env` | `GEMINI_API_KEY` and integrations | Outside workspace, read-only use. |
| `~/.local/share/jarvis/audit/` | New audit log (mode 0600) | Created on first consequential action. |
| `helix/inbox/` | User-supplied PDFs/screenshots | Untracked (added to `.gitignore`). |
| `helix/logs/` | Runtime logs | Ignored. |

No database, memory file or user document was deleted during this work. Two
smart-home files were **moved**, not deleted, and stay recoverable.

## 6. Virtual environments and caches

- `JARVIS/venv/` — the only venv used to run tests in this audit.
- `helix/ui/node_modules/` — Vite deps; ~1,026 files. **Untracked** after this audit
  (they had been accidentally committed by a broad `git add`; see CLEANUP C-9).
- `helix/ui/.vite/` — build cache; ignored.
- `__pycache__/` in both projects; ignored.

## 7. Active services (not disturbed)

| Unit | What it runs |
|---|---|
| `helix-globe.service` | Vite dev server for the God's Eye View globe |
| `helix-live.service` | HELIX Gemini Live voice proxy on `127.0.0.1:8788` |
| `hermes-gateway.service` | Hermes messaging gateway |
| `oci-a1-launch.service` | Always-free capacity hunter (unrelated to this audit) |

All four were left running. `helix-live` now loads its model/voice/persona/key from
`JARVIS/core/voice.py`; that change takes effect on the next restart, not immediately.

## 8. Inspection coverage

| Category | Coverage |
|---|---|
| JARVIS `main.py` | Full read of every region touched, plus both dispatch chains |
| JARVIS `core/`, `agent/`, `actions/`, `bridge_ws.py` | Read: the modules on the voice, agent, memory, file and bridge paths |
| JARVIS `smart_home/`, `brahma_connect/` | Read before removal (dependency-traced, then moved) |
| JARVIS `venv/`, `__pycache__/`, binaries | **Excluded** — third-party, inventoried only |
| JARVIS UI assets (`assets/`, `ui_src/`, `gui/`) | Partial — structural only |
| helix `tools/*.py` | Full read of all 18 voice/orchestration modules |
| helix `ui/` globe app | Structural only (vendored three.js) |
| gods-eye-view | Structural only (upstream, unmodified) |
| `.hermes/hermes-agent` | Manifest/commit level only (20,799 third-party files) |

Files that could not be fully read: binary assets, the 6.3 G Hermes tree, and
`JARVIS/venv/`. No claim in this audit set rests on those.
