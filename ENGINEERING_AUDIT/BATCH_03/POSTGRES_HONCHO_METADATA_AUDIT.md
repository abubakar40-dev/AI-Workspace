# PostgreSQL 18 / Honcho Metadata Audit (Phase 3 / A2)

**Authorization:** User explicitly approved A2 (privileged, metadata-only PG18/Honcho inspection: DB/role/schema/table/count/timestamp metadata; no sensitive row contents). **Method:** `psql -h /var/run/postgresql -p 5433 -U postgres` local socket, read-only SQL (`information_schema`, `pg_*` catalogs/stats, aggregate `count/min/max` on timestamp columns only). No writes, DDL, migrations, dumps, or destructive maintenance.

## Cluster identity (VERIFIED)
- `PostgreSQL 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1) on x86_64-pc-linux-gnu` (B303)
- Access path verified: local socket `/var/run/postgresql`, port 5433, user `postgres` (A2). Matches `honcho_local/honcho_server.py` connection target (`host=/var/run/postgresql port=5433 dbname=honcho user=postgres`, E03/B305).

## Databases (metadata)
| datname | owner | encoding | allowconn | size |
|---|---|---|---|---|
| honcho | postgres | UTF8 | t | 8190 kB |
| postgres | postgres | UTF8 | t | 7694 kB |
| template0 | postgres | UTF8 | f | 7537 kB |
| template1 | postgres | UTF8 | t | 7766 kB |

## Roles (metadata)
Includes `postgres` (superuser/login) and `honcho_user` (createdb/login, not superuser), plus standard `pg_*` roles. (No passwords/secrets inspected.)

## `honcho` database (metadata)
- **Extensions:** `pg_trgm` 1.6, `plpgsql` 1.0, `vector` 0.8.1 (VERIFIED).
- **Schema:** `public`.
- **Tables (all BASE TABLE, public):** `configuration`, `conclusions`, `messages`, `peers`, `scopes`, `sessions`, `workspaces`.

### Table structure (metadata only)
| Table | Key columns (names/types observed) | Notes |
|---|---|---|
| workspaces | id/uid, metadata/configuration jsonb, created_at/updated_at | conversation/session container |
| sessions | id, workspace_id, metadata/configuration jsonb, is_active, created_at/updated_at | session persistence |
| peers | id, workspace_id, metadata/configuration jsonb, created_at/updated_at | participants/entities |
| messages | id, session_id, peer_id, role, **content text**, created_at, metadata jsonb, **embedding USER-DEFINED** | message persistence; **content not selected** |
| conclusions | id, workspace_id, observed_id, observer_id, **content text**, created_at, metadata jsonb, **embedding USER-DEFINED** | derived/memory-like records; **content not selected** |
| scopes | id, workspace_id, metadata jsonb, created_at/updated_at | scope records |
| configuration | workspace_id, configuration/metadata jsonb, updated_at | config state |

### Sizes / estimated counts / safe timestamp aggregates
| Table | total size | n_live_tup (est.) | count/min/max timestamps (aggregates) |
|---|---:|---:|---|
| workspaces | 32 kB | 2 | 2 rows; created 2026-11-09 23:10:11–23:10:54; updated max 23:11:26 |
| sessions | 32 kB | 1 | 1 row; created/updated 2026-11-09 23:13:12 |
| peers | 16 kB | 0 | 0 |
| messages | 16 kB | 0 | 0 |
| scopes | 16 kB | 0 | 0 |
| conclusions | 16 kB | 0 | 0 |
| configuration | 16 kB | 0 | n/a |

## Correlation
- **Honcho server code ↔ cluster/DB:** `honcho_local/honcho_server.py` targets PG18 port 5433 DB `honcho` on local socket — **matches verified cluster/DB** (B303/B305). API routes map to workspaces/peers/sessions/scopes domain consistent with tables.
- **Hermes config:** `~/.hermes/honcho.json` points Hermes at `http://localhost:8123` (local). Hermes has an installed Honcho plugin package. This is a **configured integration path**, not proof of runtime writes.
- **AJ/JARVIS/HELIX DB config correlation:** not fully traced in this audit; no evidence in this metadata pass that other ecosystem apps share `honcho` DB, but **shared-use cannot be disproven** without app config + query-audit correlation.

## Required determinations
1. **Which cluster Honcho connects to:** **VERIFIED** — PostgreSQL 18.6 on local socket port 5433 (system cluster context from prior evidence/config).
2. **Which database Honcho uses:** **VERIFIED** — `honcho` (UTF8, owner postgres).
3. **Which tables appear to belong to Honcho:** **VERIFIED/high confidence** — `workspaces, sessions, peers, messages, conclusions, scopes, configuration` with conversation/memory/embedding structure and matching Honcho domain.
4. **Whether Hermes has a configured integration:** **VERIFIED (configured)** — `~/.hermes/honcho.json` (8123/local, key redacted) and installed `~/.hermes/plugins/honcho` package.
5. **Whether actual Hermes writes can be verified:** **NOT VERIFIED by this audit.** DB shows minimal activity (2 workspaces, 1 session, 0 messages/conclusions) at 2026-11-09 timestamps; aggregates do not identify the writer. Hermes *could* have created workspace/session metadata, but **writer identity is unproven**.
6. **Whether any other application appears to share the database:** **UNVERIFIED** — no other app writes observed via metadata; no query-origin audit performed.

**Constraint honored:** no message contents, personal records, credentials, or sensitive rows retrieved.
