# Batch 05 Evidence Register

**Date:** 2026-11-10. **Mode:** A1 read-only; A2 metadata-only Honcho counts (no content); A4 preserved. Elevated read-only port inspection approved via UI. No unauthorized mutations.

| ID | Source | Method | Result | Confidence |
|---|---|---|---|---|
| E501 | Port 8000 | elevated `ss -tlnp`, `lsof`, `/proc/973/*`, `systemctl status` (read-only) | PID 973 root `/usr/sbin/legacy-printer-app server`, `legacy-printer-app.service` enabled/active since 2026-11-06, CWD `/`, LISTEN 0.0.0.0/::8000; **non-AJ ecosystem**; auth/intent UNVERIFIED | **VERIFIED owner/bind**; auth UNVERIFIED |
| E502 | Honcho metadata (A2) | `psql -h /var/run/postgresql -p 5433 -U postgres -d honcho` counts only | `workspaces=2,sessions=1,peers=0,messages=0,conclusions=0` | VERIFIED (no content) |
| E503 | Hermes Honcho static | inspect plugin `__init__.py/sync_turn`, `session.py` save/add_message/flush, `client.py`, server endpoints | real write-capable path exists (`sync_turn` → chunk/add_message/save/background thread; `save_messages`/write frequency/init controls); runtime load/invocation/persistence **UNVERIFIED** | VERIFIED static capability; runtime UNVERIFIED |
| E504 | JARVIS source-only diff | filtered manifests + SHA256 over 259 common files (`BATCH_05/jarvis_*src*`) | 259/259 common, 0 only-old/only-nested source files; 1 content diff `./Jarvis/startup.log` (runtime log) | **VERIFIED** (filtered scope) |
| E505 | AJ/JARVIS/HELIX runtime identity | systemd user units/show/cat, repo heads/status, path diffs | AJ no mapped runtime; `jarvis-claude-gateway` inactive → missing `/home/abubakargcx/JARVIS`; `helix-live` active uses **`AI_WORKSPACE/helix/tools/live_server.py`** (99c7a38 clean, differs from home copy); `/home/abubakargcx/helix` dirty e8a64cf not active runtime; `helix-globe` active from `AI_WORKSPACE/gods-eye-view` | VERIFIED mapping (snapshot) |
| E506 | HELIX specs | locate/read headings in `AI_WORKSPACE/helix/docs/*SPEC*`, `AGENT_ARCHITECTURE.md`, `PROGRESS.md` | specs exist; feature mapping substantial but refactor intent/spec equivalence **PARTIAL/UNVERIFIED** | VERIFIED presence; mapping PARTIAL |
| E507 | Controlled Honcho delta test | not executed | would require DB writes/test traffic; needs explicit approval | **BLOCKED by safety/approval boundary** |
