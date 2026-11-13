# Network Exposure & Port 8000 Resolution (Workstream D)

**Mode:** read-only. No process termination, no firewall/binding/service/credential changes.

## Port 8000 — resolution status: **UNRESOLVED (exact blocker documented)**
| Check | Evidence (D403) | Result |
|---|---|---|
| Listener | `ss -tlnp 'sport=:8000'` | **LISTEN 0.0.0.0:8000 and [::]:8000** (Recv-Q 0, Send-Q 4096) — VERIFIED |
| Kernel socket inodes | `/proc/net/tcp*` | `00000000:1F40` inode **15942**, IPv6 `:1F40` inode **15943** — VERIFIED |
| Process owner via fd scan | bounded scan of `/proc/[pid]/fd/*` for `socket:[15942|15943]` | **NOT_FOUND_BOUNDING_SCAN** — owner not resolved from user-visible proc FDs |
| `lsof` | best-effort | no owner reported in accessible output — INCONCLUSIVE |
| Docker | `docker ps` port mappings, network inspect HostPort 8000 | **no docker mapping** — VERIFIED |
| systemd | `systemctl list-units --all` grep 8000 | **no obvious systemd unit** — OBSERVED |
| Web servers/config hints | nginx/apache/caddy grep (limited) | no obvious match — INCONCLUSIVE |

**Interpretation (INFERRED, Low/Medium):** socket exists but owning PID is not discoverable via the non-privileged/namespace-visible methods attempted (possible root/other-user namespace/container runtime edge case, or scan/visibility limitation). **Do not claim secure or benign.**

**Safe next steps (approval/system read):** privileged `ss -tlnp`/`lsof -nP -iTCP:8000 -sTCP:LISTEN` as root/capable user; inspect `/proc/<pid>` if identified; check `netstat`, `nft/iptables`, container runtimes, and app configs bound to 8000. No changes.

## Re-evaluated services (snapshot, evidence from Batch 03/04)
| Port | Bind | Owner (best evidence) | Purpose | Intentional exposure? | Auth posture (evidence) |
|---|---|---|---|---|---|
| 3000 | 127.0.0.1 | Hermes WhatsApp bridge (548360) | Hermes messaging bridge | local integration likely intentional | UNVERIFIED |
| 3200 | 127.0.0.1 | next-server, Dental Lounge standalone (913566) | unrelated app | local | UNVERIFIED (not ecosystem) |
| 3389 | `*` | gnome-remote-desktop (140279, user service) | remote desktop | possibly intentional; **externally bindable** | UNVERIFIED |
| 4173 | 127.0.0.1 | helix-globe vite (10488) | God’s Eye View dev server | local integration | dev server; auth UNVERIFIED |
| 5432 | 0.0.0.0/:: | docker-proxy `thedentallounge-db-1` | Dental Lounge PG17 | **network-exposed DB**; intent UNVERIFIED | DB creds exist (redacted); network controls UNVERIFIED |
| 5434 | 0.0.0.0/:: | docker-proxy `dental-lounge-ui-v2-db-1` | Dental Lounge UI v2 PG17 | **network-exposed DB**; intent UNVERIFIED | same |
| 8000 | 0.0.0.0/:: | **UNRESOLVED** | unknown | **UNKNOWN** | UNKNOWN |
| 8123 | 127.0.0.1 | Honcho server (893598) | local Honcho API | local integration | local API key configured (redacted); enforcement UNVERIFIED |
| 8765 | 0.0.0.0 | mamba_desktop (140470) | desktop app (unrelated) | **network-exposed**; intent UNVERIFIED | UNVERIFIED |
| 8788 | 127.0.0.1 | helix-live (10326) | Helix live proxy | local | UNVERIFIED |
| 20129 | 127.0.0.1 | OmniRush proxy (918166) | local OpenAI-compatible proxy | local (preserved) | OAuth/proxy auth UNVERIFIED |

**Risk focus:** 8000 (unknown owner/exposure), 3389 (RDP exposure), 5432/5434 (DB exposure), 8765 (exposed desktop app) — classify intent and auth before any hardening (A3/GREEN SIGNAL required for changes).
