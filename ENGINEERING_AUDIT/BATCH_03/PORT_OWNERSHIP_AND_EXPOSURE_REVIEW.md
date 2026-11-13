# Port Ownership & Exposure Review (Phase 5 / A1)

**Mode:** Read-only snapshot/correlation. No binding, firewall, service, or credential changes.

## Target ports (requested)
| Port | Bind | PID/owner | Executable/cwd (evidence) | Service/project | Auth/exposure evidence | Confidence |
|---|---|---:|---|---|---|---|
| 8000 | 0.0.0.0, [::] | **UNVERIFIED** | listener present; no docker port mapping; `/proc` fd inode scan timed out (visibility limits) | **UNVERIFIED** | externally bindable; auth/intent unknown | BLOCKED on owner |
| 8765 | 0.0.0.0 | 140470 | `/usr/bin/python3.14 -m mamba_desktop --background`, cwd `/home/abubakargcx` | mamba_desktop (user desktop app context) — **not AJ/JARVIS/HELIX/Hermes/Honcho core** | exposed bind; purpose/auth not audited here | VERIFIED owner |
| 3200 | 127.0.0.1 | 913566 | next-server v16.4.2, cwd `~/Desktop/The Dental Lounge/.next/standalone` | Dental Lounge app — **not AJ ecosystem core** | localhost only | VERIFIED |

## Re-checked externally bound services
| Port | Bind | Owner | Evidence | Auth/exposure intent |
|---|---|---|---|---|
| 3389 | `*` (all interfaces) | gnome-remote-desktop (PID 140279, user service active) | systemd/process snapshot | remote desktop may be intentional; auth/encryption/firewall/NLA not audited (read-only) |
| 5432 | 0.0.0.0/:: | docker-proxy -> `thedentallounge-db-1` (PG17) | docker inspect/ps (Batch 02/03 context) | DB network-visible; credentials exist (redacted), exposure intent UNVERIFIED |
| 5434 | 0.0.0.0/:: | docker-proxy -> `dental-lounge-ui-v2-db-1` (PG17) | docker inspect/ps | same as 5432 |

## Notes
- 8000 remains the main unresolved exposure; identifying it may require privileged process inspection or service correlation (A2/system-level read, if appropriate) — not completed in this pass.
- Do not assume 8765/3200 belong to the AI ecosystem; evidence points to mamba_desktop and Dental Lounge respectively.
