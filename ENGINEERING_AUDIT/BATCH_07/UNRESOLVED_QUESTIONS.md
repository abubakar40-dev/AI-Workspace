# Batch 07 — Unresolved Questions

Status codes: `OPEN` · `REDUCED` (narrowed, still open) · `CLOSED-BY-EVIDENCE` · `BLOCKED-ON-APPROVAL`

| ID | Question | Status | What B07 established | Resolution path |
|---|---|---|---|---|
| Q701 | Can Hermes write to Honcho at all? | `BLOCKED-ON-APPROVAL` | Root cause of the B06 failure found: Hermes used `base_url=http://localhost:8123` (Honcho) as its **LLM endpoint**, so the turn died at 404 before the memory hook. Honcho still `messages=0`. | Approved V1 (paid) or V2/V3 (config) probe per `HERMES_HONCHO_VALIDATION_PLAN_v2.md` → `A3/GREEN SIGNAL` |
| Q702 | Is `AI_WORKSPACE/AJ` the canonical control plane? | `REDUCED` | It is the only control-plane-shaped codebase; scope now specified (12 interfaces). Missing: git repo, entrypoint, executed tests. | **U2** approval of runtime scope |
| Q703 | Is `AI_WORKSPACE/JARVIS` the canonical JARVIS source? | `REDUCED` | Yes as *source* — it is the only committed tree, ahead of `master` and both backups. **B05's "backups only" finding was wrong.** | **U3** ratification + decide whether `master` later fast-forwards |
| Q704 | Is HELIX a two-line fork? | `CLOSED-BY-EVIDENCE` | No. Line A *contains* Line B's head (`e8a64cf`); Line B's uncommitted work is 69/74 byte-identical to the checkpoint commit `c68326b` on Line A. | Ref-topology decisions only: **U4** (branch of record), **U5** (5 uncommitted files) |
| Q705 | Which HELIX line runs today? | `CLOSED-BY-EVIDENCE` | `AI_WORKSPACE/helix` @ `99c7a38` via `helix-live.service` (user unit, active, `127.0.0.1:8788`). | none |
| Q706 | Is `JARVIS_ROOT` broken for `helix-live`? | `CLOSED-BY-EVIDENCE` | No. The unit points at `AI_WORKSPACE/JARVIS`, which **exists**. B05's "missing JARVIS" referred to the stale gateway unit path. | none |
| Q707 | Do AJ's 65 tests pass? | `OPEN` | Never executed — no `pytest` in system Python, `venv-honcho`, or bundled Hermes Python. Installing is out of scope. | Provide a runner (user choice) or run in the approved implementation batch |
| Q708 | Should Honcho be retained? | `OPEN` | Healthy backend, zero records after every audit batch; writer unproven. | **U7** |
| Q709 | Are `8000`/`8765`/`3389`/`5432`/`5434` intentionally exposed? | `OPEN` | All are non-ecosystem; all bind beyond loopback. Every ecosystem service is loopback-only. | **U6** intent; then A3 hardening |
| Q710 | Does `legacy-printer-app` (8000, root) have authentication? | `OPEN` | Owner established (B05, elevated read-only). Auth never demonstrated. | Owner review; A3 for any change |
| Q711 | What are the 5 uncommitted HELIX tool edits in `/home/abubakargcx/helix`? | `OPEN` | They differ from both `c68326b` and `99c7a38`; `tools/live_server.py` differs in all three states. | **U5** author review |
| Q712 | Should the shared HELIX↔JARVIS voice contract become a package? | `DEFERRED` (D3) | `07a2522` adopted the shared contract; both trees just consolidated and are still moving. | After U3/U4 settle |
| Q713 | Is `jarvis-claude-gateway.service` needed at all? | `OPEN` | Enabled, inactive, `ExecStart` points at a nonexistent path. | Decide with U3; retargeting = A3 |
| Q714 | Which exposure/branch policies should be standing rules? | `OPEN` | Evidence supports two: ecosystems stay loopback; one branch of record per project. | Ratify as policy in Batch 08 |
