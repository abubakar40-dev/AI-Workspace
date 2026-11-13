# Batch 04 — Approval Required

**Already authorized and used (no re-approval needed):** A1 read-only investigations, A2 metadata-only PG18 reuse/context, A4 non-destructive HELIX backup integrity verification (separate manifests in `BATCH_04/`; existing backup unchanged). No unauthorized mutations performed.

## Requires explicit approval / decisions
| Item | Reason | Type |
|---|---|---|
| Privileged/namespace-aware identification of port 8000 owner | non-privileged scan unresolved | approved system read / admin method |
| Controlled Hermes→Honcho metadata-delta test (isolated workspace/session; metadata-only verification) | creates test records/traffic | explicit approval |
| Disposable HELIX restore/build/test copy and any service/UI/network test runs | operational/test activity outside pure static audit | approval (scope-limited) |
| Source-only JARVIS diff/hashing at scale (if it creates large temp artifacts) | I/O/temp outputs | A1 if read-only outputs in audit dirs |
| Canonical AJ/JARVIS source/runtime selection; HELIX refactor intent; exposure intent decisions | product/architecture judgment | **user decisions** |
| Any config/permission/binding/firewall/service/DB/git/file mutation, restore, cleanup, merge, dedupe, migration, deployment | outside Batch 04 | **A3/GREEN SIGNAL** |
