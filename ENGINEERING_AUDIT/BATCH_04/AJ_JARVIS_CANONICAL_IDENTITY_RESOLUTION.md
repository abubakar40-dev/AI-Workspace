# AJ/JARVIS Canonical Identity Resolution (Workstream B)

## Scope & method (A1, read-only)
Compared: `AI_WORKSPACE/AJ`, `backup/JARVIS-old-repo-20261106`, `backup/JARVIS-nested-duplicate-20261106`, runtime/launcher evidence (Batch 03/04). Used clean sorted file manifests (D408: excl `.git`/pycache/pyc), git HEAD/status/history signals, and top-level unique-path characterization. **No coarse-count-only decision; no merge/selection.**

## Repository comparison
| Repository/path | Git | HEAD/history | Runtime status | Observed nature |
|---|---|---|---|---|
| `AI_WORKSPACE/AJ` | no git | n/a | **no verified running process** | AJ pre-Hermes foundation/control-plane code (ports/adapters style, `aj/*.py` incl. memory/orchestrator/task/config) — distinct from legacy JARVIS app |
| `backup/JARVIS-old-repo-20261106` | git, **dirty** | `cffa32d` 2026-09-26 (shared with nested) | **no verified running process** | legacy JARVIS app snapshot; **15878 files** in clean manifest; 4044 files not in nested |
| `backup/JARVIS-nested-duplicate-20261106` | git, **dirty** | same HEAD | **no verified running process** | legacy JARVIS snapshot; **11836 files**; only 2 files not in old |
| `/home/abubakargcx/JARVIS` | missing | n/a | referenced historically (e.g. helix-live `JARVIS_ROOT`) | absent path; cannot assume obsolete |

## Uniqueness/divergence (VERIFIED file-list, interpretation PARTIAL)
- **Common files:** 11834. **Only-old:** 4044. **Only-nested:** 2 (D408).
- **Only-old characterization (top paths):** predominantly `venv/lib/*` (~3956), plus `config/jarvis_browser_profile/*` (~80), `venv/share/*` (6), `chat_history/2026-11-04.md`, `2026-11-05.md`. This indicates the old-repo contains **substantial additional environment/runtime/profile/history artifacts** (and possibly source under venv only? unlikely) not present in nested. **It does NOT by itself prove more application source code.**
- **Only-nested:** two browser session files.
- **Conclusion:** repositories are **not file-identical duplicates**. However, **application-source uniqueness remains unresolved** without a manifest diff that excludes venvs/runtime profiles or a targeted source-tree diff.

## Identity/role assessment
| Component | Role (target/master context) | Canonical status | Confidence |
|---|---|---|---|
| AJ | CEO/control plane/orchestration/governance | **Unresolved active canonical runtime**; `AI_WORKSPACE/AJ` is the strongest *foundation code* candidate by intent/structure, but runtime unverified | Medium |
| JARVIS | personal assistant agent, independent project | **Unresolved**; legacy backups preserve history/artifacts, but neither mapped to active runtime and missing `/home/abubakargcx/JARVIS` confuses identity | Low/Unresolved |
| HELIX | advanced execution agent, independent | separate repo (`/home/abubakargcx/helix`), active services mapped; canonical *source state* complicated by dirty refactor | Medium (identity) / Low (state) |

## Resolution
**Canonical AJ/JARVIS identity is NOT resolved.** Evidence supports: (1) AJ foundation is architecturally distinct from legacy JARVIS app backups; (2) JARVIS backups are not identical file trees but differ largely in venv/runtime/profile artifacts; (3) no active runtime points to any candidate. **Recommendation:** keep all preserved; do not merge/delete/select canonical by recency/organization. Next required evidence: runtime launcher/config mapping to actual entrypoints, source-only diff excluding `venv`/browser profiles/caches, and explicit user decision on AJ control-plane vs legacy JARVIS app roles.
