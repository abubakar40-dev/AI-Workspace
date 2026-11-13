# Exposure Policy Ratification

**Mode:** read-only. No service, firewall, bind, or container configuration was changed. Every hardening action below is `A3/GREEN SIGNAL REQUIRED`.

Scope: the six endpoints named for ratification (`8000`, `3389`, `5432`, `5434`, `8765`) plus ecosystem-local services for contrast.

---

## 1. Live state (re-verified B07)

| Port | Bind | Owner (PID) | Owner verified by |
|---|---|---|---|
| `8000` | `0.0.0.0` + `::` | `legacy-printer-app server` (973, root) | B05 elevated inspection; process still live B07 |
| `3389` | all interfaces | `gnome-remote-desktop-daemon` (140279) | `ps` (B07) |
| `5432` | `0.0.0.0` + `::` | Docker `thedentallounge-db-1` | `docker ps` (B07) |
| `5434` | `0.0.0.0` + `::` | Docker `dental-lounge-ui-v2-db-1` | `docker ps` (B07) |
| `8765` | `0.0.0.0` | `mamba_desktop --background` (140470) | `ps` (B07) |
| `8123` | `127.0.0.1` | Honcho API (893598) | `ss` (B07) |
| `8788` | `127.0.0.1` | `helix-live` voice proxy (10326) | `ss` (B07) |
| `4173` | `127.0.0.1` | `helix-globe` Vite (10488) | `ss` (B07) |
| `20129` | `127.0.0.1` | OmniRush proxy (918166) | `ss` (B07) |
| `3000` | `127.0.0.1` | Hermes WhatsApp bridge (548360) | `ss` (B07) |
| `3200` | `127.0.0.1` | Dental Lounge `next-server` (913566) | `ss` (B07) |

**The structural observation:** every ecosystem service is loopback-bound. Every non-loopback listener belongs to a **non-ecosystem** service (system printing, remote desktop, two unrelated Docker databases, an unrelated desktop app). The exposure surface of this machine is currently *not* an AJ/JARVIS/HELIX/Hermes problem.

---

## 2. Per-endpoint ratification

### 8000 — `legacy-printer-app.service`

| Field | Finding |
|---|---|
| Ecosystem ownership | **No.** System printing service, unrelated to AJ/JARVIS/HELIX/Hermes |
| Current bind | `0.0.0.0` **and** `::` — reachable from any network the host is on |
| Intended purpose | Legacy CUPS/printer app server (per unit name) |
| Remote required? | **Unknown** — likely not; a printer service rarely needs LAN-wide HTTP |
| Auth status | **Unverified.** No authentication has been demonstrated |
| Risk | **Elevated-by-position, unknown-by-content.** A root-owned service listening on all interfaces on a developer workstation. Whether that matters depends entirely on what the app does — which nobody has established |
| Recommended posture | Bind to `127.0.0.1`, or block 8000 at the firewall if remote printing is not required. Verify whether the app has its own auth before any remote exposure is tolerated |
| Hardening requires A3? | **Yes** — unit change (`IPAddressDeny`/bind), firewall rule, or service disable are all mutations |

**Explicitly not an ecosystem fix.** It should be raised with whoever owns the host's printing setup, not folded into ecosystem hardening. `UNKNOWN — DO NOT ASSUME SAFE.`

### 3389 — `gnome-remote-desktop`

| Field | Finding |
|---|---|
| Ecosystem ownership | No (host remote-access service; *supports* ecosystem work remotely) |
| Current bind | All interfaces (daemon active, PID 140279) |
| Intended purpose | Remote desktop into this workstation |
| Remote required? | **User decision** — depends on whether the user actually remote-controls this machine |
| Auth status | Not verified in this audit (GNOME RDP uses per-user credentials/TLS; configuration not inspected) |
| Risk | **High if unused, acceptable if intended.** RDP on a workstation is a common intrusion target; an unused listener is pure surface |
| Recommended posture | If remote desktop is used: keep enabled but require TLS + strong password, restrict source networks, prefer a VPN/tunnel over open RDP. If unused: disable the service |
| Hardening requires A3? | **Yes** — service state and firewall both mutate |

### 5432 — Docker `thedentallounge-db-1` (PostgreSQL 17)

| Field | Finding |
|---|---|
| Ecosystem ownership | **No** — unrelated application database |
| Current bind | `0.0.0.0:5432->5432/tcp` + `[::]` |
| Intended purpose | Dental Lounge application database |
| Remote required? | Almost certainly **no** — the app and DB are on the same host |
| Auth status | Credentials exist (redacted, not inspected); network-level exposure is the issue, not credential strength |
| Risk | **High.** A database published on all interfaces is the single most common cause of workstation data exposure. Container-internal access needs no published port |
| Recommended posture | Remove the host port publish (`ports:` entry), or bind to `127.0.0.1:5432:5432`. The app can reach it via the Docker network or loopback without LAN exposure |
| Hardening requires A3? | **Yes** — `docker-compose`/container recreation. Also note: this is **not** the Honcho database (Honcho is PG18 on `5433`, loopback) |

### 5434 — Docker `dental-lounge-ui-v2-db-1` (PostgreSQL 17)

| Field | Finding |
|---|---|
| Ecosystem ownership | No |
| Current bind | `0.0.0.0:5434->5432/tcp` + `[::]` |
| Intended purpose | Second Dental Lounge database (UI v2) |
| Remote required? | No |
| Auth status | As above — exposure is network-level |
| Risk | **High**, identical class to 5432. Two exposed databases multiply the problem |
| Recommended posture | Same remedy: unpublish or bind to loopback |
| Hardening requires A3? | **Yes** |

### 8765 — `mamba_desktop --background`

| Field | Finding |
|---|---|
| Ecosystem ownership | No (a desktop app, not part of the AJ ecosystem) |
| Current bind | `0.0.0.0:8765` — **not** loopback-restricted, unlike the ecosystem services |
| Intended purpose | `mamba_desktop` background server |
| Remote required? | **Unknown**, probably not |
| Auth status | Unverified |
| Risk | **Medium.** A desktop application's HTTP surface on all interfaces; content/behaviour unknown to this audit |
| Recommended posture | Prefer loopback bind; if the app cannot be configured, block at the firewall |
| Hardening requires A3? | **Yes** |

---

## 3. Ecosystem services — posture confirmation (no action)

| Service | Posture | Note |
|---|---|---|
| Honcho `8123` | Loopback only — **correct** | Keep local. Auth is a shared key; enforcement beyond the key is unverified, which is acceptable while loopback-only |
| `helix-live` `8788` | Loopback only — **correct** | Unit description explicitly says "127.0.0.1 only"; matches reality |
| `helix-globe` `4173` | Loopback only — **correct** | Vite dev server; correctly not exposed |
| OmniRush proxy `20129` | Loopback only — **correct** | Operational note: runs from `/tmp/omnirush-hermes`, so it will not survive a reboot cleanly |
| Hermes bridge `3000` | Loopback only — **correct** | `--port 3000` bound locally |

**No ecosystem endpoint requires hardening right now.** The correct posture already exists; the risk sits in neighbouring services.

---

## 4. Ratification summary

| Port | Ecosystem? | Exposure required? | Auth verified? | Risk | Verdict |
|---|---|---|---|---|---|
| 8000 | No | Unknown (probably no) | No | Elevated, unknown content | Restrict or verify — **A3** |
| 3389 | No | **User decision** | Not inspected | High if unused | Decide then restrict/disable — **A3** |
| 5432 | No | No | Network-exposed | **High** | Unpublish / loopback — **A3** |
| 5434 | No | No | Network-exposed | **High** | Unpublish / loopback — **A3** |
| 8765 | No | Unknown (probably no) | No | Medium | Loopback or firewall — **A3** |
| 8123/8788/4173/20129/3000 | Yes | No | Partial (loopback mitigates) | Low | **No change** |

**Standing rule to ratify:** no ecosystem service may bind beyond `127.0.0.1` without an explicit, recorded user decision. Every ecosystem service currently complies. Any future exception is a `USER DECISION REQUIRED` + A3 change.

**What this section does not claim:** that the host is secure. It claims only that the *ecosystem* is not the source of the exposure, and that five non-ecosystem listeners need an owner's decision. No hardening was performed.
