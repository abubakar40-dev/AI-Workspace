# Port, Process & Network Ownership (Workstream B)

**Status:** Partial (current snapshot). Bindings/owners can change; no network probing or auth attempts.

## Observed listeners (selected, current snapshot E07)
| Port | Proto | Bind address | PID | Process | Path/service | Likely owner | Exposure/risk notes |
|---|---|---|---:|---|---|---|---|
| 3000 | tcp | 127.0.0.1 | 548360 | node (MainThread) | Hermes WhatsApp bridge `~/.hermes/.../whatsapp-bridge/bridge.js --port 3000` | Hermes | Localhost-only (expected for local bridge); auth/config UNVERIFIED |
| 3200 | tcp | 127.0.0.1 | 913566 | next-server v16.4.2 | UNVERIFIED (not mapped) | UNVERIFIED project | Localhost-only; owner unresolved |
| 3389 | tcp | * | 140279 | gnome-remote-desktop | systemd user service | GNOME Remote Desktop | **Externally reachable bind**; intentionality/auth/encryption/firewall UNVERIFIED — attention needed |
| 4173 | tcp | 127.0.0.1 | 10488 | node | helix-globe service (vite dev `--host 127.0.0.1 --port 4173`) from `AI_WORKSPACE/gods-eye-view` | HELIX/God's Eye View | Localhost-only per unit |
| 5432 | tcp | 0.0.0.0/:: | (docker-proxy) | docker-proxy -> `thedentallounge-db-1` | Docker postgres:17-alpine | Dental Lounge DB | **External bind**; DB credential protection/network controls UNVERIFIED |
| 5433 | tcp | 127.0.0.1 | - | system postgres18 (listener) | `/etc/postgresql/18/main` | System PostgreSQL (Honcho target on cluster) | Localhost bind; access controls in `pg_hba` UNVERIFIED |
| 5434 | tcp | 0.0.0.0/:: | (docker-proxy) | docker-proxy -> `dental-lounge-ui-v2-db-1` | Docker postgres:17-alpine | Dental Lounge UI v2 DB | **External bind**; same concerns as 5432 |
| 8000 | tcp | 0.0.0.0/:: | - | UNVERIFIED (listener present; PID not captured in compact view) | UNVERIFIED | UNVERIFIED | **External bind, unexplained owner** — P1 |
| 8123 | tcp | 127.0.0.1 | 893598 | python | `honcho_server.py` from `AI_WORKSPACE/honcho_local` (venv `~/.hermes/venv-honcho`) | Honcho | Localhost-only; Hermes points here via `honcho.json` (key redacted) |
| 8765 | tcp | 0.0.0.0 | 140470 | python | UNVERIFIED | UNVERIFIED | **External bind, unexplained owner** — P1 |
| 8788 | tcp | 127.0.0.1 | 10326 | python | helix-live systemd user service: `AI_WORKSPACE/helix/tools/live_server.py`, venv `~/.local/share/helix-live-venv`; unit sets `JARVIS_ROOT=.../AI_WORKSPACE/JARVIS` | HELIX live voice proxy | Localhost-only per intent; path ref to AI_WORKSPACE/JARVIS noted |
| 20129 | tcp | 127.0.0.1 | 918166 | node | `/tmp/omnirush-hermes/src/proxy.mjs` | OmniRush proxy (preserved) | Localhost-only |

## Expected / ecosystem-related
Hermes gateway/bridge (local/supervised), Honcho 8123, OmniRush 20129, helix-globe 4173, helix-live 8788 appear consistent with known components (VERIFIED/OBSERVED).

## Unexplained / needs attention
- **8000 (0.0.0.0/::)** and **8765 (0.0.0.0)**: owners not established in this pass. *Potentially risky until identified.*
- **3389 (gnome-remote-desktop, external bind):** may be intentional for remote desktop; auth/config/firewall not audited.
- **5432/5434 (Docker Postgres, external bind):** app DBs; exposure may be intended for local dev but is network-visible — verify auth/network policy.
- **3200 (localhost next-server):** owner unresolved.

## Approval-gated recommendations (no changes made)
1. Identify PIDs/units for 8000 and 8765; confirm purpose before any firewall/bind change.
2. Review gnome-remote-desktop and Docker Postgres exposure against actual need; changes require approval.
3. Repeat `ss`/`lsof`/unit correlation after reboot or state changes for drift.
