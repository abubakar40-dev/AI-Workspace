# Batch 03 Prioritized Action Plan

| Priority | ID | Action | Why now | Evidence | Approval |
|---|---|---|---|---|---|
| P0 | B3-1 | Resolve AJ/JARVIS canonical runtime map (launchers/configs/entrypoints → actual process or intended active path) | identity blocks safe memory/integration work | B306, AJ/JARVIS reports | A1 + user decision |
| P0 | B3-2 | Deep static trace of Hermes Honcho plugin hooks + enablement; correlate with Honcho metadata (no contents) | verifies actual memory flow possibility vs reality | B304,B305 | A1 |
| P0 | B3-3 | Identify port 8000 owner with sufficient privileges/visibility | unresolved external exposure | B306 | approved system read/A2 as needed |
| P1 | B3-4 | Clean JARVIS backup equivalence/uniqueness audit (sorted manifests, targeted hashes, dirty deltas) | prevents wrong dedupe/canonical assumptions | B307 | A1 (I/O) |
| P1 | B3-5 | HELIX spec-to-implementation map (`HELIX_BUILD_SPEC.md` vs deleted old paths vs untracked new bridge/UI) | preservation + refactor clarity | B302,B308 | A1 + user decision |
| P1 | B3-6 | Optional full checksum manifest for HELIX backup | hardens A4 verification | B302 limitation | A1 |
| P1 | B3-7 | Confirm exposure intent/auth posture for 3389/5432/5434/8765; classify 8000 after B3-3 | security risk triage | port report | user/A2 read |
| P2 | B3-8 | Draft AJ canonical memory contract (observed vs target) using Honcho schema evidence; decide adapter role | architecture convergence | A2, memory flow | user review |
| P2 | B3-9 | PG18/Honcho/Hermes backup+restore inventory and isolated restore test | data safety | U307 | approval |
| P2 | B3-10 | Any HELIX restore/cleanup/JARVIS consolidation | implementation | depends on B3-1/4/5 | **A3/GREEN SIGNAL + decisions** |

## Next batch readiness
- **Blocked until resolved:** B3-1, B3-2, B3-3 materially affect next engineering phase. B3-5 affects HELIX feature recovery. Implementation changes remain blocked by A3/user decisions.
