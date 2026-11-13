# Exposure Policy Decision Package (Workstream F)

**Read-only policy assessment. No hardening performed. Future changes require A3/GREEN SIGNAL.**

| Port | Owner | Bind | Ecosystem-owned? | Dev/local-only likely? | Required remotely? | Auth verified? | Exposure required? | Hardening recommendation | Status |
|---|---|---|---|---|---|---|---|---|---|
| 8000 | `legacy-printer-app.service` (PID 973) | 0.0.0.0/:: | No | No (system printing service) | **USER DECISION REQUIRED** | No | **UNKNOWN** | restrict bind/firewall to trusted LAN or localhost if remote not needed; verify app auth/config | **RECOMMENDED review** |
| 3389 | gnome-remote-desktop | `*` | Host service (supports ecosystem use) | No | **USER DECISION REQUIRED** | No | depends on remote access need | if needed: strong auth/VPN/NLA/firewall scope; if not: disable/restrict | **USER DECISION REQUIRED** |
| 5432 | docker PG17 `thedentallounge-db-1` | 0.0.0.0/:: | No (unrelated app) | should be local/container-only | **USER DECISION REQUIRED** | creds redacted; controls No | **usually No** | bind localhost/internal network; firewall | **RECOMMENDED review** |
| 5434 | docker PG17 `dental-lounge-ui-v2-db-1` | 0.0.0.0/:: | No | should be local/container-only | **USER DECISION REQUIRED** | No | **usually No** | same as 5432 | **RECOMMENDED review** |
| 8765 | `mamba_desktop` | 0.0.0.0 | No | likely local desktop | **USER DECISION REQUIRED** | No | **UNKNOWN** | restrict to localhost unless required | **RECOMMENDED review** |
| 8123 | Honcho server | 127.0.0.1 | Yes (memory candidate service) | Yes | No | API key configured (redacted), enforcement UNVERIFIED | No (local) | keep localhost; verify auth when exposed beyond local contracts | **RECOMMENDED** |
| 8788 | helix-live | 127.0.0.1 | Yes | Yes | No | UNVERIFIED | No | keep localhost; verify local access controls | **RECOMMENDED** |
| 4173 | helix-globe vite dev | 127.0.0.1 | Yes (separate UI app) | dev/local | No | UNVERIFIED (dev server) | No | keep localhost; do not treat as prod exposure | **RECOMMENDED** |
| 20129 | OmniRush proxy (`/tmp`, preserved) | 127.0.0.1 | Supporting integration (preserved) | local | No | UNVERIFIED | No | keep localhost; note `/tmp` durability risk (operational) | **RECOMMENDED** |
| 3000 | Hermes WhatsApp bridge | 127.0.0.1 | Yes/supporting | local | No | UNVERIFIED | No | keep localhost | **RECOMMENDED** |
| 3200 | Dental Lounge next-server | 127.0.0.1 | No | local | No | UNVERIFIED (out of scope) | No | no ecosystem action | **DEFERRED/out of scope** |

**Summary:** Localhost-bound ecosystem services (8123/8788/4173/20129/3000) appear appropriately local in snapshot; auth remains partially unverified. Externally bindable services (8000/3389/5432/5434/8765) require intent/auth review. `UNKNOWN — DO NOT ASSUME SAFE`.
