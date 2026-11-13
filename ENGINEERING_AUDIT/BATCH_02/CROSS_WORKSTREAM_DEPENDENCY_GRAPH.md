# Batch 02 Cross-Workstream Dependency Graph

## P0 dependency chain
```text
[A: Honcho→PG18:5433/honcho target VERIFIED] ──┐
                                               ├─> [D: Memory ownership] needs privileged metadata + Hermes plugin/runtime trace
[E: HELIX worktree dirty, untracked WIP] ──────┤   (blocks canonical memory integration & safe feature work)
                                               │
[C: AJ/JARVIS canonical source NOT established]┴─> [Implementation sequencing] blocked
        │
        └─> [helix-live JARVIS_ROOT ref, runtime launchers, memory stores] UNVERIFIED

[B: Ports 8000/8765/3389/5432/5434 exposure] ──> [Security posture / A3 changes need approval]
[F: 664 honcho.json perms; many secret locations] ─┘
```

## Key correlations
1. **Honcho backend (A) → memory (D):** Honcho’s likely backend is identified (PG18/5433/`honcho`), but schema/data ownership and Hermes write behavior remain unknown — cannot declare Honcho canonical memory.
2. **Canonical identity (C) → memory/architecture (D):** AJ foundation code exists, but active AJ/JARVIS runtime is unknown; memory ownership cannot be finalized until canonical owners/processes are mapped.
3. **HELIX triage (E) → preservation & roadmap:** large deletions plus untracked replacements suggest active refactor; any restore/cleanup or integration work is unsafe before backup + intent clarification.
4. **Ports/security (B,F) → A3:** external binds and unexplained services require identification before any hardening changes.
5. **OmniRush preserved (Batch 01) vs Hermes default now OpenRouter:** inference path stabilized; does not resolve memory/canonical-identity/data-ownership.

## What blocks what
| Blocker | Blocks |
|---|---|
| No privileged PG18 metadata access | Confirming Honcho schema/data ownership and cluster-wide DB owners |
| Canonical AJ/JARVIS runtime unknown | Safe migration, memory contract implementation, dedupe decisions |
| HELIX intent unclarified + no approved backup | Any HELIX cleanup/restore/commit strategy |
| Unknown 8000/8765 owners | Security hardening sign-off |
| Hermes→Honcho runtime trace missing | Confirmed memory data flow |
