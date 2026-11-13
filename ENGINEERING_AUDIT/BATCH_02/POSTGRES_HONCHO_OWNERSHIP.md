# PostgreSQL, Honcho & Database Ownership (Workstream A)

**Status:** Partial (P0 mostly resolved for Honcho backend identity; full DB metadata/backup coverage partially blocked by auth)

## Ownership matrix
| Instance | Process/container | Version | Host port | Data directory/volume | Databases (observed) | Application owner | Confidence |
|---|---|---|---|---|---|---|---|
| System PostgreSQL 18/main | `/usr/lib/postgresql/18/bin/postgres -D /var/lib/postgresql/18/main` (systemd `postgresql.service` active) | 18 (config path) | `5433` (localhost listener observed in Batch 01; config `port=5433`) | `/var/lib/postgresql/18/main` | `honcho` targeted by `honcho_server.py` (**OBSERVED/INFERRED**); full DB list **BLOCKED** for TCP password auth and not independently queried via privileged socket in this batch | **Honcho server (local)** — strong evidence | **High for Honcho target; Medium for full inventory** |
| Docker `thedentallounge-db-1` | container, healthy, docker-proxy 5432 | postgres:17-alpine | `0.0.0.0:5432`, `::5432` | volume `thedentallounge_db-data` -> `/var/lib/postgresql/data` | `dentallounge`, `dentallounge_test`, `postgres`, templates | Dental Lounge (app project name implied) | VERIFIED |
| Docker `dental-lounge-ui-v2-db-1` | container, healthy, docker-proxy 5434 | postgres:17-alpine | `0.0.0.0:5434`, `::5434` | volume `dental-lounge-ui-v2_db-data` -> `/var/lib/postgresql/data` | `dentallounge_ui_v2`, `dentallounge_ui_v2_test`, `postgres`, templates | Dental Lounge UI v2 | VERIFIED |
| Other postgres process trees (Batch 01) | PIDs 3268/3584+ patterns observed earlier | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |

## Key determinations
1. **Which PostgreSQL instance Honcho actually uses (best evidence):** System PostgreSQL 18 cluster on **port 5433**, data dir `/var/lib/postgresql/18/main`, database **`honcho`**, accessed by `AI_WORKSPACE/honcho_local/honcho_server.py` via `host=/var/run/postgresql port=5433 dbname=honcho user=postgres` (E03,E04). Honcho process (893598) is running and `/health` reports `database: connected`. **Confidence: VERIFIED target / INFERRED successful runtime path (we did not dump data or run privileged SQL).**
2. **System vs Docker vs other:** Honcho uses the **system** PG18 cluster, not the Dental Lounge Docker postgres:17 containers (different ports/owners/DB names).
3. **Database ownership:** Docker 5432/5434 are Dental Lounge app DBs (not AJ/JARVIS/HELIX/Hermes). System 5433 includes Honcho target; other DBs on that cluster **UNVERIFIED**.
4. **Genuinely different applications:** Yes, observed evidence supports separate Dental Lounge stacks and separate Honcho/system PG use.
5. **Orphaned/unused DBs:** **UNVERIFIED** (requires full DB inventory + app config correlation).
6. **Ambiguous ownership:** Other postgres process trees and non-Honcho DBs on PG18 cluster remain ambiguous.
7. **Backup coverage:** **UNVERIFIED**. Docker volumes exist on `/var/lib/docker/volumes/...`; system PG data dir exists; no backup/restore verification performed.

## Conflicts / notes
- `honcho_local/config.toml.example` shows an example Postgres URI to `localhost:5432` (E13), conflicting with actual `honcho_server.py` behavior using port 5433/socket. **CONFLICTING documentation/example vs observed code path**; treat code + runtime health as stronger evidence.

## Safety / blockers
- TCP auth to PG18 as `postgres` failed (E05). Direct privileged inspection blocked by environment. No DB writes/migrations/dumps performed.
- Container DBs queried read-only for metadata using container-provided env user; passwords redacted.

## Safe future verification plan (approval-gated where needed)
1. Read-only: inspect `pg_hba.conf`/cluster clients, list all PG18 databases/roles/sizes/connections via an authorized admin method (no data export of sensitive rows). *Requires approved access method.*
2. Correlate Honcho tables/schemas to Hermes/AJ usage (metadata only, redacted).
3. Inventory backup jobs/cron/snapshots for `/var/lib/postgresql/18/main` and Docker volumes; test restore in an isolated copy. *Requires approval and isolated environment.*
