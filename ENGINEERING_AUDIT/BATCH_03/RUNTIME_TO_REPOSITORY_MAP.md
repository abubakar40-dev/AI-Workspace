# Runtime-to-Repository Map (Phase 2 / A1)

**Snapshot:** 2026-11-10 (read-only). “Running” = observed in process/socket/systemd snapshot; “configured” = unit/config present; repo mapping is evidence-based where observable.

| Component | Status | PID | Executable / command (redacted/summarized) | Working dir / cwd | Launcher/service | Repository / source path | Confidence |
|---|---|---:|---|---|---|---|---|
| Hermes gateway | Running | 548124 | Hermes python (managed tools python) launching gateway runtime | `~/.hermes` (service context) | `hermes-gateway.service` (user, active) | `~/.hermes/hermes-agent` (codebase install) | VERIFIED |
| Hermes WhatsApp bridge | Running | 548360 | node `hermes-agent/scripts/whatsapp-bridge/bridge.js --port 3000` | (child of Hermes) | supervised by Hermes gateway | `~/.hermes/hermes-agent/scripts/whatsapp-bridge` | VERIFIED |
| Honcho server | Running | 893598 | python `honcho_server.py` (venv `~/.hermes/venv-honcho`) | started from `AI_WORKSPACE/honcho_local` (observed cmd context) | manual/background launch observed (not shown as active systemd unit in this pass) | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/honcho_local` | VERIFIED |
| OmniRush proxy | Running | 918166 | `/usr/bin/node /tmp/omnirush-hermes/src/proxy.mjs` | UNVERIFIED | `omnirush-proxy.service` active (user) | `/tmp/omnirush-hermes` (temporary path — operational risk/volatility UNVERIFIED) | VERIFIED process; repo durability UNKNOWN |
| HELIX live voice proxy | Running | 10326 | `~/.local/share/helix-live-venv/bin/python .../AI_WORKSPACE/helix/tools/live_server.py` | service default/UNVERIFIED | `helix-live.service` (user, active), binds 127.0.0.1:8788; env `JARVIS_ROOT=/run/media.../AI_WORKSPACE/JARVIS` | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/helix` | VERIFIED |
| HELIX globe / God’s Eye View dev server | Running | 10488 | node `.../gods-eye-view/node_modules/.bin/vite --host 127.0.0.1 --port 4173` | `AI_WORKSPACE/gods-eye-view` (unit) | `helix-globe.service` (user, active) | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/gods-eye-view` | VERIFIED |
| HELIX OCI A1 capacity hunter | Running/configured | 16392 | `/usr/bin/bash .../AI_WORKSPACE/helix/tools/oci-a1-launch.sh` | UNVERIFIED | `oci-a1-launch.service` (user, active) | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/helix` (script path) | OBSERVED |
| Dental Lounge next-server (3200) | Running (unrelated) | 913566 | `next-server (v16.4.2)` | `~/Desktop/The Dental Lounge/.next/standalone` | UNVERIFIED launcher | `~/Desktop/The Dental Lounge` build output | VERIFIED owner; not AJ ecosystem core |
| mamba_desktop (8765) | Running (unrelated) | 140470 | python `-m mamba_desktop --background` (mamba venv) | `/home/abubakargcx` | UNVERIFIED | mamba desktop install | VERIFIED owner; not AJ ecosystem core |
| Port 8000 listener | Running but owner unresolved | UNVERIFIED | LISTEN 0.0.0.0/::8000; no docker mapping; fd/inode scan timed out | UNVERIFIED | UNVERIFIED | UNVERIFIED | **BLOCKED (owner)** |
| gnome-remote-desktop (3389) | Running | 140279 | gnome-remote-de* | UNVERIFIED | `gnome-remote-desktop.service` (user, active) | GNOME system component | VERIFIED |
| AJ foundation (`AI_WORKSPACE/AJ`) | Installed code, **no verified running process** | - | - | - | no launcher mapped | `/run/media/abubakargcx/My Drive/AI_WORKSPACE/AJ` | OBSERVED code only |
| JARVIS legacy backups | Not active runtimes (backups) | - | - | - | n/a | `AI_WORKSPACE/backup/JARVIS-*` | VERIFIED paths; active use UNVERIFIED |
| `/home/abubakargcx/JARVIS` | Missing | - | - | - | referenced historically (e.g. helix-live `JARVIS_ROOT`) | missing path | VERIFIED missing |

## Desktop/alias notes
- `~/.local/share/applications/helix.desktop` exists (B306). Full alias/script scan not exhaustive.
- **Do not infer active identity from directory names** — AJ foundation vs legacy JARVIS backups remain unresolved for canonical runtime ownership.
