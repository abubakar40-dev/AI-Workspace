# HELIX Repository Audit (Batch 01, partial)

## Evidence (VERIFIED/OBSERVED)
- Repo: `/home/abubakargcx/helix`, git `main...origin/main`. Worktree is dirty: modified `.gitignore`, `bridge/README.md`, `docs/PROGRESS.md`, `docs/VOICE_AUDIO_DIAGNOSTIC.md`, `tools/selfcheck.py`; deleted `bridge/server.py`, deploy service file, many `tools/check-*`/diagnostic scripts, and `ui/*` console/shell/agent-town/voice-core files (sampled from `git status --short`).
- Tracked files include `agents/pc.md`, `bridge/*`, `docs/*` (HELIX build spec, progress, diagnostics, bug notes), `inbox/*` artifacts, and `tools/*` (browser/eras/gesture/app/selfcheck/orb/town/webgl related names appear in index/history context from `git ls-files`). No top-level manifest found in quick scan (`pyproject.toml`/`package.json`/`requirements*` not found at maxdepth 2).
- Master doc requires preserving HELIX capabilities: God’s Eye View, real-time news, Books of Eras, research, Hermes-related functionality, existing interfaces/automation — **feature health UNVERIFIED**; worktree deletions raise regression risk and must be understood before any cleanup/restore decisions (**REQUIRES USER APPROVAL**).

## Key findings
- **P1:** Dirty/deleted state in active HELIX repo; preserve all local work. Do not reset/clean.
- **P1:** Missing obvious packaging/dependency manifest at repo root (or not detected) complicates reproducible test/run audit.
- **UNVERIFIED:** Runtime entry points, God’s Eye View/news/Books of Eras functionality, Hermes integration, voice status (master doc requested temporary deactivation concept; implementation unverified), permissions/safety, tests.

## Safe next steps (Category A)
1. Read `docs/HELIX_BUILD_SPEC.md`, `docs/PROGRESS.md`, `agents/pc.md`, and `tools/selfcheck.py` diff to understand intended/current state.
2. Locate actual UI/bridge implementations (some paths deleted in worktree but may exist in index/history or elsewhere).
3. Inventory runnable components and safe non-destructive checks only.
