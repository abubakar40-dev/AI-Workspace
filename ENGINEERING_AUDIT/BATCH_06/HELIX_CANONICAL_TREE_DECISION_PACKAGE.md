# HELIX Canonical Tree Decision Package (Workstream C)

**No merge/restore/checkout performed.** Evidence artifacts: `helix_tree_divergence.txt`, `helix_wip_consolidation_map.txt`.

## C1. Compared trees (corrected with verified git ancestry)
| Attribute | `AI_WORKSPACE/helix` | `/home/abubakargcx/helix` |
|---|---|---|
| Branch / HEAD | `audit/consolidation-2026-11-06` → `99c7a38` | `main` → `e8a64cf` |
| Working tree | clean (0 porcelain) | dirty (42 porcelain = 17 M/A, 22 D, …) |
| HEAD dates | `2026-11-06 12:09` | `2026-10-18 20:15` |
| Runtime use | **Active**: `helix-live.service` runs `.../AI_WORKSPACE/helix/tools/live_server.py` (8788) | **Not active** for helix-live |
| Ancestry | **`e8a64cf` IS an ancestor of `99c7a38`**; `rev-list --left-right --count e8a64cf...99c7a38` = `0  3` (home has **0** commits the workspace lacks) | Same history, 3 commits behind |
| Unique commits | `c68326b` "Checkpoint: pre-consolidation working state on an audit branch", `07a2522` "Consume the shared JARVIS voice contract…", `99c7a38` "Point the live diagnostic at the same model the proxy uses" | none |

### Commit-level change set `e8a64cf..99c7a38`
`25 A / 24 D / 9 M` — i.e. the branch **commits the same deletions and the same new files that exist as uncommitted WIP in the home tree**, then adds further edits.

### Home WIP vs workspace HEAD content map (42 entries)
| Result | Count | Paths |
|---|---:|---|
| SAME (byte-identical) | 17 | `bridge/README.md`, `bridge/bridge_ws.py`, `bridge/helix.desktop`, `bridge/helix_desktop.py`, `docs/PROGRESS.md`, `docs/VOICE_AUDIO_DIAGNOSTIC.md`, `docs/ADD_AN_AGENT.md`, `docs/AGENT_ARCHITECTURE.md`, `docs/PACKAGING_PLAN.md`, `install.sh`, `uninstall.sh`, `tools/selfcheck.py`, `tools/lms_client.py`, `ui/build.js`, `ui/helix-ui.html`, `ui/package.json`, `ui/package-lock.json` |
| DIFFERS (workspace newer) | 3 | `.gitignore`, `ui/src/`, `ui/node_modules/` (build cache — not meaningful) |
| MISSING from workspace | 22 | **all 22 are deletions the home WIP itself made** (`bridge/server.py`, `deploy/helix-gesture.service`, 13 × `tools/*` legacy check/geometry/gesture scripts, 8 × `ui/agent-town|console|shell|voice-core|world-monitor` pages) — the branch commits the identical deletions |

**Interpretation:** no WIP file is unrepresented. Every home-WIP addition is present verbatim in the workspace tree; every home-WIP deletion is also committed there; the only genuine content differences (`ui/src/`, `.gitignore`, live/voice tools) are **newer** in the workspace.

## C2. Relationship classification (corrected)
| Tree | Classification | Confidence |
|---|---|---|
| `AI_WORKSPACE/helix` @ `99c7a38` | **Active runtime tree AND the committed successor of the home WIP** (consolidation audit branch) | **High (VERIFIED via ancestry + content map)** |
| `/home/abubakargcx/helix` @ `e8a64cf` + WIP | **Stale pre-consolidation working tree**: its WIP was carried forward into the audit branch; nothing unique remains except 2 uncommitted diffs (`ui/src`, `.gitignore`) of unclear provenance | **High** |
| Relationship | **Linear successor, not divergent lines.** Earlier B06 wording ("separate/diverged lines") is **superseded** by this evidence | High |

Residual caveat: `ui/src/` differs and `.gitignore` differs (home has uncommitted edits that the branch does not contain) — so the home tree is *not* worthless, but it is **not a competing development line**.

## C3. Strategy options
| Option | Description | Assessment | Label |
|---|---|---|---|
| A | Continue development from `AI_WORKSPACE/helix` | Matches active runtime, clean, contains the consolidated WIP + 3 further commits | **RECOMMENDED** |
| B | Use `/home/abubakargcx/helix` as development source and reconcile later | Its WIP is already in the audit branch; would reintroduce stale/deleted surfaces and duplicate effort | **NOT RECOMMENDED** |
| C | Treat as separate lines indefinitely | Would preserve a tree whose unique content is 2 small uncommitted diffs; adds reconciliation debt | **DEFERRED only as archival posture** |
| D | New canonical branch from `99c7a38` after user sign-off | Clean way to formalize the canonical line without merging | **RECOMMENDED follow-up action (mutation — needs A3)** |

## Recommendation
**RECOMMENDED (high confidence):** treat `AI_WORKSPACE/helix` (`audit/consolidation-2026-11-06` @ `99c7a38`) as the **canonical HELIX development and runtime baseline**. Treat `/home/abubakargcx/helix` as an **archival pre-consolidation working tree** whose WIP is fully carried forward; do not resume development there. Before any archival disposition, review the two residual uncommitted diffs (`ui/src/`, `.gitignore`) — a cheap, non-destructive diff review settles whether anything there is still wanted.

**Still USER DECISION REQUIRED:** (a) ratify this canonical line; (b) whether to promote the audit branch to a proper canonical branch name (git mutation — A3); (c) disposition of the home tree (archive/leave as-is — no deletion authorized).
