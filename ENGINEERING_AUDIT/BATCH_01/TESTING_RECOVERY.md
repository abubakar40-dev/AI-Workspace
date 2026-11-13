# Testing, Reliability & Recovery (Batch 01)

## Executed (safe)
- Hermes default chat smoke test was verified earlier in this conversation context (`PONG`, exit 0, no `--provider/-m`) after approved config fix. No additional paid/API tests run in this batch.
- Health checks: Honcho `/health` OK; OmniRush `/health` OK (read-only).

## Not executed
- JARVIS/HELIX/AJ unit/integration/e2e suites, DB tests, memory persistence tests, automation tests, permission tests, recovery/restore tests. Reasons: canonical environments/paths ambiguous, mutation/external/API risk possible, missing local pytest in system Python for AJ quick run.

## Critical untested paths (INFERRED)
Startup/config validation across AJ/JARVIS/HELIX, provider failover in real Hermes fallback chain, Honcho↔Hermes↔AJ memory persistence/provenance, task lifecycle/cancellation, permission gates for consequential actions, backup restore, Wayland desktop automation.

## Strategy (proposal)
Prioritize: config/startup smoke checks (no side effects) → provider request with approved no-cost tests → memory persistence read/write in isolated test data → task lifecycle → permissions → recovery/restore drills in copies → delegation → automation.
