# Redacted Security & Configuration Inventory (Workstream F)

**Status:** Partial. No secrets exposed; no exploitation/scanning/auth attempts; no permission/firewall/service changes.

## Secret-handling observations (redacted)
| Path | Type | Present | Permissions/owner (observed) | Referenced by | Exposure risk notes |
|---|---|---|---|---|---|
| `~/.hermes/.env` | env secrets | yes | `600 abubakargcx` | Hermes runtime | Local file; content not read |
| `~/.hermes/auth.json` | auth config/tokens | yes | `600` | Hermes | Sensitive |
| `~/.hermes/honcho.json` | local API config/key | yes | **`664`** (group/other readable bits set) | Hermes→Honcho | **Risk: looser perms than 600**; value redacted (`[REDACTED_LOCAL_KEY]`) |
| `~/.hermes/config.yaml` | config | yes | `600` | Hermes | OK |
| `~/.config/Hermes/secure-token-storage.json` | tokens | path found | UNVERIFIED | Hermes desktop? | not inspected |
| OmniRush token stores (`~/.config/omnirush/*`, `~/.omnirush*/*`) | OAuth/API tokens | paths found | UNVERIFIED | OmniRush | preserve; not read |
| `~/.git-credentials` | git credentials | path found | UNVERIFIED | git | sensitive; not read |
| `AI_WORKSPACE/honcho_local/.env` | env | path found | UNVERIFIED | Honcho local | not read |
| Dental Lounge project `.env*` under `~/Desktop/The Dental Lounge/` | app envs | paths found | UNVERIFIED | Dental Lounge | outside core ecosystem but present |

## Network/exposure security matrix (partial)
| Component | Config location | Authentication | Permissions | Network exposure | Secret handling | Risk | Evidence |
|---|---|---|---|---|---|---|---|
| Honcho (8123) | `~/.hermes/honcho.json`, `honcho_local/honcho_server.py` | local API key configured (redacted); enforcement in server **UNVERIFIED** | process user-owned | localhost only (OBSERVED) | key in 664 file | Medium (local) | E07,E08 |
| Hermes gateway/bridge | `~/.hermes/*`, user service | UNVERIFIED (bridge/messaging auth model not audited) | mostly 600 | bridge localhost:3000 | tokens in hermes state/config paths | Medium | E07,E12 |
| OmniRush proxy | `/tmp/omnirush-hermes/src/proxy.mjs` | OAuth cached (health reports) | UNVERIFIED | localhost:20129 | token stores exist | Medium | E07 |
| Docker Postgres 5432/5434 | container env/configs | DB credentials exist (redacted) | container/volume managed | **0.0.0.0/:: exposed** | env passwords redacted | **Medium-High** (network-visible DBs) | E06,E07 |
| GNOME Remote Desktop 3389 | system/user GNOME service | UNVERIFIED | UNVERIFIED | **external bind (*)** | UNVERIFIED | **Medium-High** depending on config | E07 |
| Unknown services 8000/8765 | UNVERIFIED | UNVERIFIED | UNVERIFIED | **0.0.0.0 exposed** | UNVERIFIED | **High until identified** | E07 |
| helix-live 8788 | user service unit | UNVERIFIED | user service | localhost | references `JARVIS_ROOT` path | Low-Medium | E07,E12 |

## Observations
- Central permission enforcement across AJ/JARVIS/HELIX/Hermes: **UNVERIFIED** (AJ foundation has permission concepts in code; runtime use unknown).
- Shell/MCP/desktop/browser execution restrictions: **UNVERIFIED**.
- Audit trails for agent actions: **UNVERIFIED**.
- Logs/argv secret leakage: not systematically scanned (avoid reading sensitive logs); Honcho server code contains a Postgres connection with user in source — **code/config secret hygiene review recommended** (redacted finding).
- `helix-live.service` sets `JARVIS_ROOT=/run/media.../AI_WORKSPACE/JARVIS` — path existence under that exact subpath **UNVERIFIED**; potential config drift.

## Approval-gated recommendations
1. Tighten `~/.hermes/honcho.json` permissions to `600` after confirming no dependent process requires broader access. *A2/A3 judgment if service interaction needed.*
2. Identify/auth-audit externally bound 8000/8765/3389/5432/5434; restrict bindings/firewall only with approval.
3. Full redacted secret/config inventory including ownership/age/usage; never centralize secret values.
