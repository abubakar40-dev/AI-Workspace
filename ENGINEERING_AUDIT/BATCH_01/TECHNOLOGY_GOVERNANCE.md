# Technology Governance (Batch 01, partial)

## Target (master doc, current direction/finalized where noted)
- Modular monolith first; Ports & Adapters; capability registry; central config/logging/audit; provider-independent memory; no Docker for target architecture; no local LLM in current production (adapter compatibility preserved).

## Observed reality
- Docker daemon and Postgres containers (`thedentallounge-db-1`, `dental-lounge-ui-v2-db-1`) are active/healthy — **legacy/external dependencies possible; inspect before removal**.
- Multiple Postgres trees (system postgres18 + docker postgres17). Hermes gateway/WhatsApp bridge/Node/Python runtimes active. Honcho running from workspace code with separate venv.
- HELIX has no obvious root manifest detected in quick scan; AJ foundation is stdlib-oriented per README. JARVIS canonical repo/path ambiguous.

## Violations/risks (OBSERVED/INFERRED)
- Operational complexity on 8GB hardware (multiple DBs, browsers/Electron, Hermes, dev servers). Docker present despite target direction — not a violation to remove blindly; **governance gap** until owners mapped.
- Uncommitted work across repos; path migration incomplete. Architecture boundaries (ports/adapters/permission enforcement) not verified in runtime JARVIS/HELIX.

## Decisions requiring user approval
- Any dependency addition/removal, framework adoption, service consolidation, Docker/Postgres decommission, migration, or architectural refactor.
