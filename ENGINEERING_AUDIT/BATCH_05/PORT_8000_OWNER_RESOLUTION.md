# Port 8000 Owner Resolution (Workstream A)

**Method:** A1 read-only; privileged read-only inspection approved via elevation UI for `ss`/`lsof`/`/proc`/`systemctl status` (no process/config/firewall/bind changes).

## Result: **RESOLVED (owner identified)**

| Property | Evidence | Result | Confidence |
|---|---|---|---|
| PID | `ss -tlnp` (elevated), `lsof -nP -iTCP:8000 -sTCP:LISTEN` | **973** | VERIFIED |
| Executable | `/proc/973/exe` readlink | `/usr/sbin/legacy-printer-app` | VERIFIED |
| CWD | `/proc/973/cwd` | `/` | VERIFIED |
| Parent | `ps -p 973 -o ppid` | **1** (systemd/init) | VERIFIED |
| Service | `systemctl status 973` / `legacy-printer-app.service` | **`legacy-printer-app.service`** (loaded, enabled, active/running since Fri 2026-11-06 17:48:26 PKT) | VERIFIED |
| Container | docker mappings checked (Batch 04/05 context) | **no docker container mapping** | VERIFIED |
| Project | service/exe/cmdline | **Not AJ/JARVIS/HELIX/Hermes**; system legacy printer application (`/usr/sbin/legacy-printer-app server`) | VERIFIED (non-ecosystem) |
| Purpose | service name/cmdline/journal hint | Legacy printer application; journal shows SNMP broadcast-address warning — printing/discovery behavior implied | OBSERVED/INFERRED |
| Authentication | no config/auth audit performed | **UNVERIFIED** | UNVERIFIED |
| Exposure | `ss`: LISTEN `0.0.0.0:8000`, `[::]:8000`; inodes 15942/15943 | **Network-exposed on all interfaces** (intent UNVERIFIED) | VERIFIED bind; intent UNVERIFIED |

## Interpretation
Port 8000 is owned by a **system printer service** (`legacy-printer-app`), unrelated to the AJ ecosystem. Exposure is real (all interfaces). **Do not label safe** without evidence of intended exposure and authentication/authorization controls. No changes made.

## Prior blocker status
Batch 04’s “owner unresolved” blocker is **resolved for owner attribution**; **security intent/auth remains UNVERIFIED** and should be treated as `UNKNOWN — DO NOT ASSUME SAFE` for exposure decisions.
