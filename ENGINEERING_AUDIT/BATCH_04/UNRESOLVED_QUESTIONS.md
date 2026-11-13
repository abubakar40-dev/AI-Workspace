# Batch 04 Unresolved Questions

| ID | Question | Why unresolved | Impact | Safe next step | Approval |
|---|---|---|---|---|---|
| Q401 | Who owns/listens on port 8000 (0.0.0.0/::, inodes 15942/15943)? | non-privileged/namespace-visible methods did not reveal PID; no docker/systemd/web-server match | security/exposure blocker | privileged `lsof/ss` or namespace-aware inspection; app config audit | system read/approved method |
| Q402 | Does Hermes actually load the Honcho plugin at runtime and write conversation messages? | static integration present; Honcho has 0 messages and writer not attributable | canonical memory flow | static hook trace; approved controlled metadata-delta test | A1 + controlled test approval |
| Q403 | What is the canonical active AJ runtime/source? Is `AI_WORKSPACE/AJ` intended as active control plane replacing/coordinating legacy JARVIS? | no active runtime mapped; `/home/abubakargcx/JARVIS` missing | identity blocker | launcher/entrypoint/config map + user decision | A1 + user decision |
| Q404 | Which JARVIS backup contains unique *application source* (excluding venv/runtime profiles)? | file-list diff shows old-only bulk in venv/profile/history; source-only diff not completed | preservation/canonical risk | sorted source-only manifest/hash diff excluding generated/runtime dirs | A1 (I/O) |
| Q405 | Is HELIX refactor intentional and does `bridge_ws.py`/`ui/src` satisfy `HELIX_BUILD_SPEC.md` vs deleted implementations? | intent/spec mapping incomplete | HELIX recovery/integration | spec-to-entrypoint mapping; disposable-copy validation | A1 + user decision |
| Q406 | Exposure intent/auth for 3389, 5432, 5434, 8765, 8000? | bindings known; intent/auth not fully audited | security | intent confirmation + read-only auth/firewall review | user/system read |
| Q407 | Should Honcho become AJ-governed canonical memory adapter, and under what provenance/retention contract? | backend/schema capable; flow unproven | architecture decision | complete Q402 evidence; draft/approve contract | user/architecture review |
