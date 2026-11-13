# Batch 03 Master Report — Preservation, Runtime Identity & Memory-Flow Investigation

**Project:** AJ / JARVIS / HELIX / Hermes / Honcho  
**Mode:** A1 read-only, A2 metadata-only PG18/Honcho, A4 non-destructive HELIX backup (all explicitly approved by user).  
**Output:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/ENGINEERING_AUDIT/BATCH_03/`  
**Constraints honored:** no source/config/permission/service/DB mutations, no git mutations, no cleanup/deletion/merge/migration, no sensitive row contents, no paid API/UI tests, no auth bypass. Direct `sudo -n` wrapper was refused by environment; A2 completed via authorized local socket `psql -U postgres` (metadata-only).

## 1. What AJ/JARVIS/HELIX/Hermes code is actually running, and from where?
**VERIFIED (snapshot, B306/B308):**
- **Hermes gateway** (548124, `hermes-gateway.service`) / **WhatsApp bridge** (548360, port 3000) — `~/.hermes/hermes-agent`.
- **Honcho** (893598, port 8123) — `AI_WORKSPACE/honcho_local/honcho_server.py` via `~/.hermes/venv-honcho`.
- **OmniRush proxy** (918166, port 20129) — `/tmp/omnirush-hermes/src/proxy.mjs` (durability UNKNOWN).
- **HELIX live** (10326, 8788) — `AI_WORKSPACE/helix/tools/live_server.py` (`helix-live.service`, `JARVIS_ROOT` env ref to missing `AI_WORKSPACE/JARVIS` path — impact UNVERIFIED).
- **God’s Eye View/helix-globe** (10488, 4173) — `AI_WORKSPACE/gods-eye-view` via `helix-globe.service`.
- **HELIX OCI launcher** (16392) — `AI_WORKSPACE/helix/tools/oci-a1-launch.sh`.

**Not AJ ecosystem core / unrelated:** 8765 `mamba_desktop` (140470), 3200 Dental Lounge next-server (913566). **Unresolved:** port 8000 listener owner. **No verified running AJ foundation or legacy JARVIS app process** from `AI_WORKSPACE/AJ` or JARVIS backups; `/home/abubakargcx/JARVIS` missing.

## 2. Is the HELIX backup complete and verified?
**VERIFIED with documented exclusions/limitations (A4).** Backup: `AI_WORKSPACE/backup/HELIX-backup-20261109T211343Z-batch03`. Includes `.git`, tracked/modified/untracked project files and relevant repo state; source unchanged. Exclusions only generated caches (`ui/node_modules`, `__pycache__`, `.pytest_cache`, `*.pyc`). Manifest diff showed only expected excluded paths. **Limitation:** full SHA256 checksum manifest and total-byte metric not generated. See `HELIX_BACKUP_VERIFICATION.md`.

## 3. Which PostgreSQL cluster and database back Honcho?
**VERIFIED (A2).** PostgreSQL 18.6 on local socket `/var/run/postgresql`, port 5433, database `honcho` (UTF8, owner postgres, ~8190 kB). Matches Honcho server code and runtime health.

## 4. What tables and metadata does Honcho maintain?
**VERIFIED (A2 metadata, no content).** Schema `public`: `workspaces, sessions, peers, messages, conclusions, scopes, configuration`. Extensions: `vector`, `pg_trgm`, `plpgsql`. Columns include ids, workspace/session/peer relations, role, `content` (text), metadata/configuration (jsonb), `embedding` (USER-DEFINED), timestamp fields. Aggregates: 2 workspaces, 1 session, 0 peers/messages/scopes/conclusions/configuration rows (timestamps 2026-11-09). See `POSTGRES_HONCHO_METADATA_AUDIT.md`.

## 5. Is Hermes-Honcho integration enabled?
**Configured/installed: VERIFIED.** Hermes has `~/.hermes/honcho.json` pointing to `http://localhost:8123` (local, key redacted) and an installed Honcho plugin package in `~/.hermes/plugins/honcho`. **Runtime activation flag/actual plugin execution:** **UNVERIFIED**.

## 6. Is there evidence that Hermes has actually written to Honcho?
**NOT VERIFIED.** Honcho DB contains minimal metadata (2 workspaces, 1 session; no messages/conclusions). Aggregates/timestamps do not identify the writer; Hermes is only one possible configured client. No writer attribution claim is made from config alone.

## 7. Does AJ have a functioning canonical memory implementation?
**NOT VERIFIED.** `AI_WORKSPACE/AJ` contains `aj/memory.py` and control-plane foundation concepts, but no active process/service was mapped to it as the ecosystem’s canonical memory owner. Hermes local state and Honcho exist but canonical ownership/provenance/raw-record contract remain unresolved.

## 8. Which JARVIS backup contains unique work?
**UNRESOLVED/PARTIAL.** Both backups share HEAD `cffa32d` and similar coarse counts; a quick `comm` sample (imperfect due sort warnings) suggested differing runtime/profile/chat_history paths. **Cannot declare identical or select a canonical backup.** Preserve both; perform clean sorted manifest+hash+dirty-delta audit (B3-4).

## 9. Which HELIX features are at preservation risk?
**High risk (state verified, intent UNVERIFIED):** deleted tracked `bridge/server.py`, `deploy/helix-gesture.service`, many diagnostics/tools, and large old UI surfaces (`ui/console`, `ui/shell`, `ui/voice-core`, `ui/world-monitor`, `ui/agent-town`). **Untracked WIP now preserved in backup** (highest priority): `bridge_ws.py`, `helix_desktop.py`, `ui/src`, build/package/html files, new docs, install/uninstall scripts, `tools/lms_client.py`. God’s Eye View service runs separately from `gods-eye-view`; Helix live proxy runs from `helix/tools/live_server.py`. Full spec-feature mapping remains incomplete (`HELIX_FEATURE_PRESERVATION_MAP.md`).

## 10. What remains unknown?
Port 8000 owner; Hermes→Honcho actual runtime writes/writer identity/enablement; canonical AJ/JARVIS active runtime/source; JARVIS backup unique-delta truth; HELIX refactor intent/spec equivalence; other PG18 DB application owners beyond inspected metadata; Honcho/shared-DB query-origin; backup/restore adequacy; exposure intent/auth for 3389/5432/5434/8765/8000; helix-live `JARVIS_ROOT` validity.

## 11. Which findings block the next engineering phase?
- **Identity block:** canonical AJ/JARVIS runtime/source unresolved.
- **Memory-flow block:** Hermes→Honcho actual writes and AJ canonical memory ownership unverified.
- **Security/exposure block:** port 8000 owner and exposure intent unresolved.
- **Preservation/refactor block:** HELIX intent/spec mapping unresolved (backup reduces loss risk but not design clarity).
- **A3 boundary:** any cleanup/restore/hardening/migration/config changes remain blocked pending decisions and GREEN SIGNAL.

## Evidence and confidence
Primary register: `EVIDENCE_REGISTER.md`. Confidence is high for A2 Honcho DB/cluster/schema metadata, HELIX backup completion (with documented exclusions), and observed runtime owners for mapped processes; medium/partial for Hermes runtime activation and JARVIS backup equivalence; low/unverified for writer identity, canonical AJ/JARVIS runtime, and port 8000 ownership.
