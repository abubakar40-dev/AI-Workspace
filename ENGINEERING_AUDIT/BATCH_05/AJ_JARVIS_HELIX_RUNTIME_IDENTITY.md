# AJ/JARVIS/HELIX Runtime Identity (Workstream C)

**Method:** A1 read-only. Evidence chain: service/launcher → ExecStart/entrypoint → process/workdir/path → repo/config. No service/config changes.

## C1. AJ (`AI_WORKSPACE/AJ`)
- **Contents:** `aj/` package, `config/`, `docs/`, `schemas/`, `tests/`, `README.md`; no obvious `main.py`/CLI launcher found at top levels searched. No git repo.
- **Runtime:** no verified running process mapped to `AI_WORKSPACE/AJ` (Batch 03/04/05 runtime scans).
- **Assessment:** **development foundation / dormant codebase (static)**; **not runtime-verified active**. Role aligns with AJ control-plane intent, but canonical/active runtime unresolved. Confidence: **Medium (static), Low (runtime)**.

## C2. JARVIS
- **`/home/abubakargcx/JARVIS`:** **missing** (historical ref).
- **`jarvis-claude-gateway.service`** (`~/.config/systemd/user/jarvis-claude-gateway.service`): `ExecStart=/home/abubakargcx/JARVIS/scripts/start-claude-gateway.sh`; `ActiveState=inactive`, `SubState=dead`. **VERIFIED inactive**; points to missing path — **not an active JARVIS runtime**.
- **Backups (`old-repo`/`nested-duplicate`):** git dirty, same HEAD `cffa32d` historically; **no running process mapped**. Application-source filtered comparison shows 259/259 common, 1 content diff (`startup.log`) — **source-equivalent by filter; runtime-artifact differences remain in full trees**. Canonical status: **historical/preserved, unresolved for activation**.

## C3. HELIX
| Path/Service | Entrypoint / ExecStart | Source path used | Runtime status | Notes |
|---|---|---|---|---|
| `helix-live.service` | `/home/abubakargcx/.local/share/helix-live-venv/bin/python "/run/media/abubakargcx/My Drive/AI_WORKSPACE/helix/tools/live_server.py"`; env `HELIX_LIVE_PORT=8788`, `JARVIS_ROOT=/home/abubakargcx/JARVIS` | **`AI_WORKSPACE/helix`** (workspace repo) | **active user service / runtime mapped (B305)** | `AI_WORKSPACE/helix` is git `99c7a38`, **clean** (0 porcelain). `live_server.py` **differs** from `/home/abubakargcx/helix/tools/live_server.py`. Missing `JARVIS_ROOT` ref risk UNVERIFIED. |
| `/home/abubakargcx/helix` | (worktree) | local home repo | **not the active helix-live source**; **dirty** (42 porcelain), HEAD `e8a64cf` | preserved by Batch 03 backup (SHA256 verified B04). Contains untracked WIP/deletions per prior audits. |
| `helix-globe.service` | `/usr/bin/npm run dev -- --host 127.0.0.1 --port 4173` in `WorkingDirectory=/run/media/abubakargcx/My Drive/AI_WORKSPACE/gods-eye-view` | **`AI_WORKSPACE/gods-eye-view`** | **active** (B305) | **Separate application** from Helix core codebase; serves World Monitor/God’s Eye View APIs in dev mode. |
| Hermes gateway | `hermes-gateway.service` active (B305) | Hermes install/config (`~/.hermes`, system/user paths) | active | separate runtime, not AJ/JARVIS/HELIX repo identity. |

## Final matrix
| System | Source path | Entrypoint | Runtime status | Active? | Role | Confidence |
|---|---|---|---|---|---|---|
| AJ | `AI_WORKSPACE/AJ` | no mapped runtime entrypoint found | static code only | **No (verified unmapped)** | control-plane foundation candidate | Medium static / High no-runtime-mapped |
| JARVIS (legacy backups) | `backup/JARVIS-old-repo-20261106`, `.../JARVIS-nested-duplicate-20261106` | none mapped | preserved snapshots, source-equivalent by filter | **No** | historical assistant codebase | High (inactive) / Medium (equivalence scope) |
| JARVIS gateway launcher | `/home/abubakargcx/JARVIS/...` (missing) | `jarvis-claude-gateway.service` → missing script path | `inactive/dead` | **No** | stale/broken launcher ref | VERIFIED |
| HELIX live proxy | `AI_WORKSPACE/helix` | `tools/live_server.py` via `helix-live.service` | running (B305 snapshot) | **Yes (mapped)** | Helix voice/live proxy runtime | High |
| HELIX home worktree | `/home/abubakargcx/helix` | none mapped active | dirty dev/refactor tree, backup preserved | **No active runtime mapped** | WIP/refactor source; preservation target | High (not active runtime) / Medium (intent) |
| God’s Eye View globe | `AI_WORKSPACE/gods-eye-view` | `vite dev` via `helix-globe.service` | running | **Yes** | separate World Monitor app used by Helix context | High |
