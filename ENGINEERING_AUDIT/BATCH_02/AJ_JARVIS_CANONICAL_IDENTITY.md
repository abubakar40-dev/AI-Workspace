# AJ/JARVIS Canonical Identity & Source of Truth (Workstream C)

**Status:** **CANONICAL SOURCE NOT YET ESTABLISHED** (P0). Evidence is sufficient to rule out simple naming assumptions but insufficient to declare one active canonical codebase.

## Candidate inventory
| Candidate | Exists | Type | Git | HEAD / history (sampled) | Key evidence |
|---|---:|---|---|---|---|
| `/home/abubakargcx/JARVIS` | No | expected home path (master doc) | n/a | missing | Path absence confirmed (E10, Batch 01) |
| `/run/media/abubakargcx/My Drive/AI_WORKSPACE/AJ` | Yes | AJ pre-Hermes foundation | **no git repo** | n/a | README “AJ — Pre-Hermes Foundation”, control-plane modules (`permissions/capability/task/audit/config/contracts/orchestrator/agents/execution/providers/memory/calling`), 18 py files under `aj/`, 54 files total (excluding cache), README claims 65 stdlib tests; **not the same shape as legacy JARVIS app** |
| `AI_WORKSPACE/backup/JARVIS-old-repo-20261106` | Yes | legacy JARVIS app backup | git, dirty | `cffa32d` 2026-09-26 (23 commits) | `requirements.txt`, app dirs (`actions/agent/core/gui/dashboard/memory/tools/tests/venv` etc.), uncommitted mods/deletions; ~2158 files excl. venv/git/cache |
| `AI_WORKSPACE/backup/JARVIS-nested-duplicate-20261106` | Yes | legacy JARVIS backup copy | git, dirty | same HEAD `cffa32d` as old-repo | Appears near-duplicate by HEAD/count sample; **full file-level diff not completed** |
| `/home/abubakargcx/helix` | Yes | separate HELIX project | git dirty | `e8a64cf` 2026-10-18 | Independent project; not JARVIS/AJ source |

## Comparison (evidence-based)
| Candidate | Git status | Latest commit | Unique features (observed) | Shared files | Missing features | Architecture maturity | Preservation risk |
|---|---|---|---|---|---|---|---|
| `AI_WORKSPACE/AJ` | no git | n/a | AJ ecosystem control-plane foundation per README/master-doc alignment (ports/adapters, governance/orchestration primitives) | naming/docs themes with AJ/JARVIS context; not a copy of legacy JARVIS tree | legacy JARVIS UI/voice/desktop app capabilities not present as same codebase | **targeted foundation**, runtime/active use unverified | Medium (no git history in place) |
| `JARVIS-old-repo` backup | dirty | cffa32d 2026-09-26 | legacy JARVIS application structure/features implied by dirs | similar to nested copy | unknown vs “most complete” historical state; may differ from workspace AJ | legacy app snapshot; health unknown | **High** (uncommitted work) |
| `JARVIS-nested-duplicate` backup | dirty | cffa32d 2026-09-26 | likely duplicate of old-repo | likely high overlap | same as above | unknown | **High** (uncommitted work) |

## Findings
1. **Best match to current AJ identity/governing doc:** `AI_WORKSPACE/AJ` aligns with the AJ control-plane/foundation direction (separate from JARVIS app codebase identity), but **active runtime use is UNVERIFIED**.
2. **Most complete legacy JARVIS implementation:** likely one/both backup repos contain the fuller historical JARVIS app tree, but **which is authoritative and whether either is current is UNVERIFIED**.
3. **`AI_WORKSPACE/AJ` is:** a **foundation/control-plane codebase candidate** (per README/content), not proven active production JARVIS assistant and not merely documentation. **Canonical/active status UNVERIFIED.**
4. **Unique code/history in backups:** backups have git history and uncommitted changes; **must be preserved**. Nested may duplicate old-repo but dirty states can diverge — **full diff required before any dedupe decision**.
5. **Divergence:** AJ foundation and legacy JARVIS backups are **architecturally different** codebases, not simple copies.
6. **Missing `/home/abubakargcx/JARVIS`:** could indicate migration/incomplete move/obsolete path; **cannot conclude obsolete safely**.
7. **Evidence needed to establish canonical source:** (a) identify which process/service/UI/user workflow currently launches “JARVIS/AJ”; (b) find active config/DB/state paths and which repo they reference; (c) compare dirty deltas in both JARVIS backups and against any live copy; (d) run safe tests in isolated envs for AJ foundation and candidate JARVIS app; (e) explicit owner decision mapping AJ control plane vs JARVIS assistant codebase.

## Preservation requirements
- **Do not move/merge/rename/delete** any candidate. Preserve `AI_WORKSPACE/AJ`, both JARVIS backups (including uncommitted work and venvs until assessed), and HELIX separately.
- Any future dedupe of nested backup requires **GREEN SIGNAL** after full diff/backup verification.

## Recommended next step (read-only)
Resolve active runtime/config ownership: search systemd user units, shell aliases, desktop launchers, recent command history files (if present/readable), and config files for `JARVIS`, `aj`, entrypoint scripts, and absolute paths. Then produce a runtime-to-repo map.
