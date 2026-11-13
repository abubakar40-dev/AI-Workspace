# Migration Inspection Report — JARVIS Ecosystem

**Task:** t_38a3e1c8  
**Date:** 2026-11-03  
**Host:** Linux (7.0.0-38-generic)

---

## 1. Block Devices & Filesystems (`lsblk -f`)

| Device | FSType | Label | UUID | FSAVAIL | FSUSE% | Mountpoints |
|--------|--------|-------|------|---------|--------|-------------|
| loop0–loop23 | squashfs | — | — | 0 | 100% | /snap/* |
| sda1 | ntfs | System Reserved | 3428E3EF28E3AE54 | — | — | — |
| sda2 | ext4 | — | a5bbc499-9dc9-45f3-8bb1-be2730fe5043 | 6G | 90% | / |
| sda3 | ntfs | — | 2EDA826DDA82315F | — | — | — |
| **sda4** | **ntfs** | **My Drive** | **6A5ACA195AC9E245** | **49.8G** | **50%** | **/run/media/abubakargcx/My Drive** |

---

## 2. External Drive Mount Status

- **Mount point:** `/run/media/abubakargcx/My Drive` ✅ **MOUNTED**
- **Device:** `/dev/sda4`
- **Filesystem:** ntfs (ntfs3, read-write)
- **Size:** 100G
- **Used:** 51G (51%)
- **Available:** 50G
- **findmnt confirms:** `rw,nosuid,nodev,relatime,uid=1000,gid=1000,acl,iocharset=utf8,prealloc`

---

## 3. Source Directories to Migrate

| Path | Exists | Size | Notes |
|------|--------|------|-------|
| `/home/abubakargcx/JARVIS` | ✅ | **1.9G** | Main JARVIS repo — Python source, configs, tests, assets |
| `/home/abubakargcx/helix` | ✅ | **83M** | Helix ecosystem — scripts, docs, UI, tools, bridge |
| `/home/abubakargcx/gods-eye-view` | ✅ | **499M** | God's Eye View — Node.js app with node_modules, src, dist |
| `/home/abubakargcx/.hermes` | ✅ | **6.5G** | Hermes Agent config, cache, databases (eras.db ~15MB), hermes-agent dir |
| `/home/abubakargcx/.local/share/helix-live-venv` | ✅ | **70M** | Python virtualenv for Helix live proxy |
| `/home/abubakargcx/.local/share/helix-stt` | ✅ | **143M** | Helix STT — whisper-cli binary + models |

**Total estimated migration size:** ~9.2G (well within the 50G available on the external drive)

---

## 4. Running Services

### Active (running)

| Service | Status | Description |
|---------|--------|-------------|
| `hermes-gateway.service` | enabled, running | Hermes Agent Gateway — Messaging Platform Integration |
| `helix-globe.service` | enabled, running | God's Eye View globe (vite dev server) for Helix World Monitor |
| `helix-live.service` | enabled, running | Helix Gemini Live voice proxy (127.0.0.1 only) |

### Disabled

| Service | Status | Description |
|---------|--------|-------------|
| `jarvis-claude-gateway.service` | disabled | Jarvis Claude Gateway (not running) |

### Transient

| Unit | Status | Description |
|------|--------|-------------|
| `hermes-worker-kanban-t_38a3e1c8-run-154.scope` | active | Current kanban worker session |

---

## 5. Summary

- External drive **mounted** at `/run/media/abubakargcx/My Drive` (ntfs, 100G, 50G free)
- All 6 source directories confirmed present with sizes totaling ~9.2G
- 3 user services running: hermes-gateway, helix-globe, helix-live
- 1 service disabled: jarvis-claude-gateway
- System root (`/`) on sda2 (ext4) is 90% full with only 6G free — migration off the root partition is advisable