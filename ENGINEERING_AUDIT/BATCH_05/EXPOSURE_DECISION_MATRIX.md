# Exposure Decision Matrix (Workstream G)

**Read-only. No firewall/bind/service/config changes.** `UNKNOWN — DO NOT ASSUME SAFE` where evidence is insufficient.

| Port | Owner | Bind | Purpose | Authentication | External exposure | Intent | Risk | Evidence |
|---|---|---|---|---|---|---|---|---|
| 8000 | `legacy-printer-app` (PID 973, root, system service) | `0.0.0.0`, `::` | system legacy printer app (non-AJ ecosystem) | **UNVERIFIED** | **Yes (all interfaces)** | **UNKNOWN** | **HIGH/UNKNOWN** — exposed service with unverified auth | B05 port resolution |
| 3389 | `gnome-remote-desktop` (user service, B03) | `*` (observed) | remote desktop | **UNVERIFIED** | **Potential/Yes by bind** | **UNKNOWN** (may be intentional) | **HIGH/UNKNOWN** | B03/B04 |
| 5432 | docker-proxy `thedentallounge-db-1` (PG17) | `0.0.0.0`, `::` | Dental Lounge DB (non-AJ ecosystem) | creds exist (redacted); network controls **UNVERIFIED** | **Yes** | **UNKNOWN** | **HIGH** — DB exposed | B03/B04 |
| 5434 | docker-proxy `dental-lounge-ui-v2-db-1` (PG17) | `0.0.0.0`, `::` | Dental Lounge UI v2 DB | **UNVERIFIED** | **Yes** | **UNKNOWN** | **HIGH** — DB exposed | B03/B04 |
| 8765 | `mamba_desktop --background` (B04) | `0.0.0.0` | desktop app (unrelated) | **UNVERIFIED** | **Yes** | **UNKNOWN** | **MEDIUM/HIGH** | B04 |
| 8123 | Honcho server (893598, B03) | `127.0.0.1` | Honcho local API | local API key configured (redacted); enforcement **UNVERIFIED** | **No (localhost bind)** | likely local integration | **LOW/MEDIUM** (local) | B03/B04/B05 |
| 8788 | helix-live (10326) via `AI_WORKSPACE/helix/tools/live_server.py` | `127.0.0.1` | HELIX live/voice proxy | **UNVERIFIED** | **No** | likely local integration | **LOW/MEDIUM** | B03/C3 |
| 4173 | helix-globe vite dev (10488) `AI_WORKSPACE/gods-eye-view` | `127.0.0.1` | God’s Eye View dev server/APIs | dev server; auth **UNVERIFIED** | **No** | local dev integration | **LOW/MEDIUM** | B03/C3 |
| 20129 | OmniRush proxy (918166) from `/tmp/omnirush-hermes` | `127.0.0.1` | local OpenAI-compatible proxy (preserved) | proxy/auth behavior **UNVERIFIED**; Hermes OmniRush model path blocked by provider 403 earlier | **No** | local preserved integration | **LOW/MEDIUM** | B03/prior Hermes audit |
| 3000 | Hermes WhatsApp bridge (548360) | `127.0.0.1` | Hermes messaging bridge | **UNVERIFIED** | **No** | likely local integration | **LOW/MEDIUM** | B03 |
| 3200 | Dental Lounge next-server standalone (913566) | `127.0.0.1` | unrelated web app | **UNVERIFIED** (out of ecosystem scope) | **No** | local | **LOW** (ecosystem) | B04 |

**Notes:** For 8000/3389/5432/5434/8765, exposure is evidenced by bind/listener; **intent and authentication remain unresolved** — `UNKNOWN — DO NOT ASSUME SAFE`. Any hardening requires A3/GREEN SIGNAL.
