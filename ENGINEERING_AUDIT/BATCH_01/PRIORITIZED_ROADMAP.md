# Prioritized Roadmap (Batch 01)

Ranking: impact, severity, effort, risk, dependencies, reliability gain, long-term value. Labels: P0–P3/BACKLOG. All implementation changes require explicit approval as scoped.

## Top 20 (highest value)
| # | Pri | Task | Category | Evidence/Root issue | Depends on | Effort | Risk |
|---:|---|---|---|---|---|---:|---|
| 1 | P0 | Map Postgres instances (system 18/5433, docker 5432/5434, unknown trees) to owners, data dirs, configs, clients; map Honcho DB backend | A | Multiple PG trees; Honcho “DB connected” source unknown | none | M | low (read-only) |
| 2 | P0 | Identify canonical active JARVIS/AJ codebase and path strategy (`/home/JARVIS` missing, AJ workspace, backups dirty) | A | Missing home path, ambiguous copies | none | M | low |
| 3 | P0 | Hermes↔Honcho memory contract audit: what Hermes writes/reads, session store, provenance, overlap with AJ memory target | A | `honcho.json` + healthy Honcho; ownership unverified | 1 partially | M | low |
| 4 | P1 | HELIX dirty worktree triage: classify modified/deleted files vs intended state using build spec/progress; no restore/reset | A | many deletions/mods in git status | none | M | low |
| 5 | P1 | Produce metadata migration matrix for HELIX home/workspace and JARVIS/AJ candidates (no active DB/WAL checksum on live files) | A | migration incomplete claim; dirty repos | 2 | M | low |
| 6 | P1 | Port/service ownership map for exposed listeners (8000,8765,5432,5434,3389 etc.) and auth posture | A | several 0.0.0.0/:: listeners | 1 | S | low |
| 7 | P1 | Security inventory (redacted): secret/config file locations, permissions, logging redaction patterns | A | creds exist across Hermes/OmniRush/Honcho/project envs | none | M | low |
| 8 | P1 | Safe AJ foundation test run (verify test isolation, then run stdlib tests in controlled env) | A | AJ claims 65 tests; not run | 2/test env | S | med if isolation unclear |
| 9 | P1 | Hermes fallback/provider plan (proposal only): OpenRouter primary, next candidate after credential+approved smoke test | B-prep | single-provider runtime risk; fallback supported natively | 3, provider approval | S | low |
| 10 | P1 | Canonical memory design record (raw/structured/summary/provenance/Obsidian nav/backup-restore) | B-prep | master doc requirement; implementation unverified | 1,3 | M | low |
| 11 | P1 | Shared task contract + delegation lifecycle draft (AJ/JARVIS/HELIX/Hermes) | B-prep | integration gap | 10 | M | low |
| 12 | P2 | HELIX architecture/feature inventory (God’s Eye View, news, Books of Eras, research, Hermes hooks) with evidence | A | preservation required; health unknown | 4 | L | low |
| 13 | P2 | JARVIS legacy backup feature/tech debt inventory (read-only) | A | backups dirty; code value unknown | 2 | L | low |
| 14 | P2 | Desktop automation environment verification (Wayland/AT-SPI/portal/wl-clipboard) + controlled harmless UI test plan | A/A7 | master doc: broken until tested | approval for UI tests | M | med |
| 15 | P2 | Hermes resource/health hardening assessment (gateway/bridge memory, supervisor, traced-process historical concern) | A | high RSS on 8GB host | none | S | low |
| 16 | P2 | Backup & restore drill plan for Honcho/Hermes/AJ/JARVIS/HELIX stores (no destructive action) | B-prep | 3-2-1 required; unverified | 1,3 | M | low |
| 17 | P2 | Provider capability matrix update with official-doc verification dates (OpenRouter/Gemini/NVIDIA/Groq/Cloudflare target disambiguation) | A | time-sensitive unknowns | user approval for tests | M | low |
| 18 | P3 | Path-hardcoding scan and abstraction design (`/home/abubakargcx/JARVIS`, old roots) — report only | A/B-prep | missing home path | 2,5 | M | low |
| 19 | P3 | Technology overlap/dependency rationalization report (Docker/Postgres/dev servers) — no removal | A | operational complexity | 1,6 | M | low |
| 20 | BACKLOG | Implement approved modular boundaries, provider gateway, memory service, automation adapters, skill lifecycle, platform expansion | C | target architecture | 9–19 + approvals | XL | high |

## Recommended first engineering batch (compatible, read-only / low-risk)
Execute together (all Category A, no config/DB/service changes): **#1 Postgres/Honcho DB owner map, #2 canonical JARVIS/AJ path identification, #3 Hermes↔Honcho memory contract audit, #4 HELIX dirty-worktree triage, #6 exposed-port ownership map, #7 redacted security inventory**. These resolve the main unknowns blocking safe migration, memory correctness, and provider/fallback decisions.

## Sequencing constraints
- #9/#17 live provider tests depend on explicit approval and credentials/billing clarity.
- #5/#18 migration/path changes depend on #2 and GREEN SIGNAL where destructive/path-altering.
- #14 UI automation tests depend on A7 approval and disposable target.
- Any Docker/Postgres/service consolidation depends on #1/#6 and A3/A4 approvals.
