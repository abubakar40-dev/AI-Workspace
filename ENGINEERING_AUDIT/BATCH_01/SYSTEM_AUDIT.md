# System & Runtime Audit (Batch 01)

**Snapshot:** 2026-11-10T01:47:53+05:00. **Evidence:** `_system_snapshot.txt`, `_runtime_snapshot.txt`, `_docker_postgres_snapshot.txt`, `_hermes_honcho_omnirush.txt`.

## Host/resources (VERIFIED/OBSERVED)
- Host: `Wick`, Linux `7.0.0-42-generic` #42-Ubuntu SMP PREEMPT_DYNAMIC, x86_64. Uptime ~3 days 7:59, load avg `2.00, 1.52, 1.62`.
- CPU: Intel i5-7300U @ 2.60GHz, 2 cores / 4 threads, 1 socket.
- Memory: 6.9GiB total, 4.3GiB used, 478MiB free, 2.9GiB buff/cache, 2.6GiB available (snapshot).
- Swap: `/swap.img` 4.0GiB, **2.4GiB used** / 1.6GiB free (OBSERVED). Historical master doc reported 3.9GiB used on 2026-11-05 — improved but still material; cause not isolated. **Do not clear swap or kill processes without evidence.**
- Disk: `/` (sda2) 135G, 106G used, 23G avail (83%). AI_WORKSPACE drive (`/dev/sda4`) 100G, 35G used, 66G avail (35%).

## Notable processes (OBSERVED)
- Hermes gateway: PID 548124, `~/.hermes/tools/python-3.14.9+20261021-linux-x64/bin/python3 ... hermes_cli.main ... gateway run` (high RSS in sample ~411MB). Hermes WhatsApp bridge: PID 548360, Node 26.12.1, `bridge.js --port 3000 --session ~/.hermes/whatsapp/session --mode self-chat`. Supervisor `process_supervisor.sh` present.
- Honcho: PID 893598 (`python -u honcho_server.py`, ppid 893596 bash launcher) running from `AI_WORKSPACE/honcho_local`, venv `~/.hermes/venv-honcho` (OBSERVED from runtime snapshot). Health OK on `127.0.0.1:8123`.
- OmniRush proxy: PID 918166, `/usr/bin/node /tmp/omnirush-hermes/src/proxy.mjs`, listening `127.0.0.1:20129`, health OK.
- High consumers include Freebuff/Electron renderers, Chrome renderers/GPU, GNOME Shell, `next-server v16.4.2` (PID 913566), opencode-cli, OmniRush `bwrap` sandbox processes (present, not modified). Hermes gateway/WhatsApp bridge resource usage is notable on 8GB-class hardware — **INFERRED reliability risk under load**.

## Ports/listeners (OBSERVED, non-exhaustive)
- `5432/tcp`, `5434/tcp` exposed (Docker Postgres containers). `5433/tcp` localhost listener present. `8123` Honcho (localhost). `20129` OmniRush (localhost). `3000` Hermes WhatsApp bridge (localhost). `3200` next-server. `8000` exposed on all interfaces (owner UNVERIFIED from this snapshot alone). `8765` python exposed. `8788` localhost python. `4173` Vite-like dev port (localhost). `3389` gnome-remote-desktop. Multiple Freebuff/local service ports on localhost. **Security note:** services bound to `0.0.0.0`/`::` require ownership/risk review (UNVERIFIED risk level per service).

## Docker (OBSERVED) — inspect before any removal
- `dockerd` running; docker-proxy for 5432/5434. Containers: `thedentallounge-db-1` (postgres:17-alpine, Up 3 days healthy, 5432), `dental-lounge-ui-v2-db-1` (postgres:17-alpine, Up 3 days healthy, 5434), plus exited `heuristic_neumann`, `eloquent_clarke`, `stirling-pdf`. **Master doc:** no Docker for current target architecture, but existing usage must not be removed blindly. **REQUIRES USER APPROVAL / inspection** before any Docker changes.

## PostgreSQL (OBSERVED) — multiple trees
- System service `postgresql.service` active (exited) since 2026-11-09 21:49:05 PKT. Postgres 18/main processes present (`/usr/lib/postgresql/18/bin/postgres -D /var/lib/postgresql/18/main -c /etc/postgresql/18/main/postgresql.conf`, plus workers/checkpointer/wal/autovacuum/replication launcher). Localhost `5433` listening.
- Additional `postgres`/worker processes (PIDs 3268,3271,3584+ pattern) observed; parent ownership/data dirs not fully resolved in this pass.
- Docker postgres:17 containers on 5432/5434 (healthy).
- **Conclusion:** multiple PostgreSQL instances/roles likely coexist (system + Docker app DBs; possibly others). **UNVERIFIED** mapping to Honcho/JARVIS/HELIX. Honcho reports DB connected but this audit did not identify which Postgres/SQLite/DB URL it uses. **P0 investigation (read-only):** map each instance’s config/data dir/port/client.

## Gaps / not completed
- Per-PID service ownership (systemd user units, launchers), cgroup/memory attribution, `smem` swap-by-process, open files for DB WAL paths, network exposure validation, and correlation of ports 8000/8765/8788/4173/3200 to specific projects.
