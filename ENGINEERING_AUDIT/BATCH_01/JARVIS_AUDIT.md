# JARVIS/AJ Repository Audit (Batch 01, partial)

## Evidence
- `/home/abubakargcx/JARVIS` **missing** (VERIFIED). Master context lists it as a project root.
- `AI_WORKSPACE/AJ/` exists (not a git repo). README describes “AJ — Pre-Hermes Foundation” (control plane, ports/adapters, permissions/capability/task/audit/config/contracts/orchestrator/memory/provider/calling modules, `tests/` 65 tests claimed stdlib-only). **Not verified by running tests in this pass** (system `python3 -m pytest` unavailable; AJ README references `../JARVIS/venv/bin/python` which is absent).
- `AI_WORKSPACE/backup/JARVIS-old-repo-20261106/` and `JARVIS-nested-duplicate-20261106/` contain git repos with substantial uncommitted modifications/deletions (OBSERVED). Contents suggest prior JARVIS app structure (`agent/`, `agents/`, `actions/`, `core/`, `gui/`, `dashboard/`, `memory/`, `tools/`, `tests/`, `venv/`, etc.). Deep feature-by-feature health **UNVERIFIED**.

## Key findings
- **P0 (identity/location):** Canonical active JARVIS/AJ codebase is ambiguous. AJ foundation in workspace may be the intended AJ control-plane layer per master doc’s 2026-11-07 update, but relationship to historical JARVIS repo/backups is **UNVERIFIED**.
- **P1 (data safety):** Backups contain dirty git worktrees and venvs; preserve all. No destructive cleanup.
- **UNVERIFIED:** Entry points, runtime status, integrations, voice/UI, memory DBs, permissions enforcement, provider usage, test pass/fail, security issues.

## Safe next steps (Category A)
1. Identify which codebase is authoritative/active (AJ foundation vs JARVIS backup vs other).
2. Inventory manifests, entry points, env/config refs, and absolute paths (`/home/abubakargcx/JARVIS`) across AJ/JARVIS copies.
3. Run AJ tests only in an approved, isolated environment with available pytest (no network/DB mutation expected per README claim) — **requires verification of test safety first**.
