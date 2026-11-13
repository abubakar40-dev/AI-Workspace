# Batch 05 — Approval Required

**Already authorized and used (no repeated approval needed):** A1 read-only investigations (process/repo/config/runtime/static trace, manifests/hashes), A2 metadata-only Honcho count recheck (no sensitive contents), A4 preservation posture respected (existing HELIX backup unchanged; BATCH_05 created separate analytical artifacts only). Port 8000 privileged read-only inspection was performed via elevation UI approval (read-only). **No unauthorized mutations performed.**

## Requires explicit approval / decisions
| Item | Reason | Type |
|---|---|---|
| Controlled Hermes→Honcho metadata-delta test (synthetic, isolated; metadata-only verification) | creates DB records/test traffic (database writes) — **not performed** in Batch 05 | explicit approval (scope-limited) |
| Review/hardening decisions for exposed services (8000 legacy-printer-app, 3389 RDP, 5432/5434 Docker PG, 8765 mamba_desktop) | intent/auth unknown; any change is out of scope | user/system decision; **A3/GREEN SIGNAL** for changes |
| Canonical AJ runtime/source and AJ↔legacy JARVIS role | architecture/product identity decision | **user decision** |
| HELIX canonical working source and refactor/recovery intent (`AI_WORKSPACE/helix` vs `/home/abubakargcx/helix` WIP) | spec equivalence/intent unresolved | **user decision** |
| Disposable HELIX copy for spec compliance/build/runtime validation | safe only if separate and non-modifying; build/runtime tests may need resources/services | scoped approval |
| Canonical memory direction (AJ raw-first + Honcho adapter vs Honcho canonical) | depends on unresolved writer proof/governance | **user/architecture decision** |
| Any source/config/permission/bind/firewall/service/DB schema-data mutation, git mutation, restore/merge/delete, deployment, paid API calls | outside Batch 05 | **A3/GREEN SIGNAL** |
