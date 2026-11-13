# Batch 06 — Approval Required

**Already authorized and used (no repeated approval):** A1 read-only investigation; A2 metadata-only Honcho inspection; A4 non-destructive disposable HELIX copy at `BATCH_06/helix_home_disposable/` (originals + existing backup untouched). **Controlled Hermes→Honcho writer test not executed** due to misrouting/safety/DB-write constraints; documented as inconclusive. No source/config/service/network/git/DB mutations.

## Approval / decisions needed
| Item | Reason | Boundary |
|---|---|---|
| Controlled Hermes→Honcho metadata-delta validation | proves/disproves runtime writer; creates DB records/test traffic. **Requires a zero-cost completed turn**: either an approved local model server (service change) or explicit approval for one minimal paid OpenRouter call | **explicit approval + safe test plan** |
| Give AJ a runnable baseline (dependency manifest, venv/local dev env) so its 6 test suites can be executed | currently cannot be installed, tested or launched; `pytest` absent | **A3 scope for first foundation batch** |
| Canonical AJ runtime/source + minimal entrypoint/activation scope | no mapped AJ runtime; identity affects all implementation | **USER DECISION REQUIRED** |
| JARVIS role/source for future work (preserve backups; no merge) | no active runtime; backups source-equivalent filtered | **USER DECISION REQUIRED** |
| Canonical HELIX working line | **Tree relationship now RESOLVED** (`e8a64cf` ancestor of `99c7a38`; home WIP already committed). Only ratification + optional branch rename (git mutation, A3) and home-tree archival disposition remain | **USER DECISION REQUIRED (ratification)** |
| Memory direction: Candidate A (AJ raw-first canonical, Honcho adapter/index) | recommended, not proven end-to-end | **USER DECISION REQUIRED** |
| Exposure intent/hardening for 8000/3389/5432/5434/8765 (and auth verification for local services) | intent/auth unknown | **user/system decision; A3/GREEN SIGNAL for changes** |
| Any source/config/service/DB schema-data mutation, git mutation, merge/restore/cleanup, deployment, paid API calls | outside B06 scope | **A3/GREEN SIGNAL** |
