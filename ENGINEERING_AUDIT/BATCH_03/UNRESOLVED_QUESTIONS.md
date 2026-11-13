# Batch 03 Unresolved Questions

| ID | Question | Status | Safe next step | Approval |
|---|---|---|---|---|
| U301 | Who owns port 8000 (0.0.0.0/::)? | UNRESOLVED | privileged `lsof`/`ss -p`/socket-owner correlation or systemd/docker/app inventory | A2/system read as appropriate |
| U302 | Has Hermes actually written to Honcho, and with what IDs/provenance? | UNRESOLVED | static hook trace in `~/.hermes/plugins/honcho`; correlate Hermes session metadata timestamps to Honcho aggregates; controlled isolated metadata-delta test | A1 (+ controlled test approval) |
| U303 | What AJ/JARVIS code is the canonical/active runtime? | UNRESOLVED | map desktop/alias/launcher/config/entrypoint references to concrete paths; user decision | A1 + user decision |
| U304 | Are JARVIS backups truly duplicates or do dirty/runtime trees contain unique work? | PARTIAL | clean sorted manifest+hash diff (excluding caches) and dirty-delta review | A1 (I/O) |
| U305 | Is HELIX’s deletion of bridge/server/UI intentional replacement by `bridge_ws.py`/`ui/src`? Do new paths satisfy build-spec features? | UNRESOLVED | read `HELIX_BUILD_SPEC.md`/architecture/progress; map imports/entrypoints; run safe checks in isolated copy | A1 + user decision |
| U306 | Do any other apps share PG18 `honcho` DB or other cluster DBs? | UNVERIFIED | app config search + PG `pg_stat_activity`/log correlation (metadata-level, privileged if needed) | A2 |
| U307 | Backup/restore for PG18 `honcho` and Hermes state? | UNVERIFIED | inventory backup mechanisms; test restore in isolated environment | approval |
| U308 | Is helix-live `JARVIS_ROOT=/run/media.../AI_WORKSPACE/JARVIS` valid/needed? | UNVERIFIED | inspect `live_server.py` behavior and target path | A1 |
| U309 | Exposure intent/auth for 3389/5432/5434/8765? | UNVERIFIED | confirm user/system intent; auth/config/firewall read-only review | user/A2 |
