# Repository Structure Report

## 1. What the structure was

```
AI_WORKSPACE/
├── JARVIS/                 ← repo (master @ cffa32d), 133 dirty entries
│   └── JARVIS/             ← a SECOND full clone of the same repo, same commit,
│                             untracked inside the first. 1.5 G.
├── HERMES/                 ← 6.3 G copy of the Hermes tree, same commit as
│                             .hermes/hermes-agent, identical .env size
├── .hermes/hermes-agent/   ← the tree the live services actually use
├── helix/                  ← repo (main @ e8a64cf), 42 dirty entries
├── gods-eye-view/          ← repo (main @ 0dbde1e)
├── backup/, DATA/, LMS Docs/
```

Three separate ambiguities, all real:

1. **`JARVIS/JARVIS/`** — a nested clone at the same commit as its parent. `git status`
   in `JARVIS/` listed it as `?? JARVIS/`. Anything that walked the tree could read either
   copy. `diff` of the two trees was 4,113 lines and every difference was `.git/index`
   plus `venv/` binaries — the *source* was identical, so the outer tree is authoritative
   and the inner one was pure duplication.
2. **`HERMES/` vs `.hermes/`** — same commit `bf0203a794`, identical `.env` size
   (26,692 B). `HERMES/` had the newer mtime. No file in either project referenced the
   workspace copy: `hermes-gateway.service` and the HELIX tools read `~/.hermes`, which is
   `.hermes/`. A full `diff -rq` did not finish inside 120 s over 6.3 G, so authority was
   established by *reference* (what runs points at `.hermes`), not by a byte comparison.
3. **`JARVIS/Jarvis/`** — a casing variant of the project name that contains only
   `startup.log` (3,965 B). It is a log directory, not a project root. It is harmless but
   it is exactly the kind of thing a glob-based tool trips over.

## 2. What was done

| Action | From | To | Reversible by |
|---|---|---|---|
| Moved | `JARVIS/JARVIS/` | `backup/JARVIS-nested-duplicate-20261106/` | `mv` back |
| Moved | `HERMES/` | `backup/HERMES-workspace-duplicate-20261106/` | `mv` back |

Nothing was deleted. Both moves are same-filesystem renames, so they are instant and
lossless, and the full history of both copies is intact inside the moved directories.

`JARVIS/Jarvis/` was **kept**. It holds a startup log, it is not source, and removing it
would delete a diagnostic record for no structural gain. It is documented here so the
next person does not mistake it for a second project.

## 3. What the structure is now

```
AI_WORKSPACE/
├── JARVIS/            ← one authoritative root, branch audit/consolidation-2026-11-06
│   ├── core/          ← capability registry, policy, audit, confirmation, voice contract
│   ├── agent/         ← planner + executor + runtime (policy-gated tool execution)
│   ├── agents/        ← specialist agent definitions
│   ├── actions/       ← tool implementations called by the dispatcher
│   ├── tools/         ← auxiliary clients (LMS, diagnostics)
│   ├── dashboard/     ← mobile/command dashboard + bridge
│   ├── memory/, chat_history/   ← runtime data (not source)
│   ├── config/        ← settings + secrets (untracked)
│   ├── tests/         ← 17 files, 357 test functions
│   └── venv/          ← Python 3.14.4 (not tracked)
├── helix/             ← one authoritative root, independent history
│   ├── tools/         ← orchestrator, voice transports, eras, selfcheck
│   ├── bridge/        ← HTTP/WS bridge for the UI
│   ├── ui/            ← Vite globe (God's Eye View), node_modules untracked
│   ├── agents/, docs/, logs/, inbox/
├── gods-eye-view/     ← upstream dependency, unmodified
├── audit/             ← this audit set
├── backup/            ← tarballs + the two relocated duplicates
├── DATA/, LMS Docs/
└── .hermes/           ← live Hermes install
```

## 4. Structure rules this now satisfies

- One authoritative repository root per project. ✔
- No repository nested inside another outside `backup/`. ✔
- No duplicate project copy at the top level. ✔
- No casing variant that looks like a project root. ✔ (`Jarvis/` is a log dir)
- Internal module boundaries kept: JARVIS is still a modular monolith with
  `core/` → `agent/` → `actions/` → adapters. Nothing was flattened. ✔
- Runtime data, configuration and artifacts are separate from source. ✔
- Shared-component ownership is explicit: the voice contract lives in JARVIS and HELIX
  imports it; it was not copied into a third "shared" directory with no owner. ✔

## 5. Deliberately not changed

- **Git histories.** `JARVIS` and `helix` still have their own roots, branches and
  commits. No merge, no squash, no rewrite.
- **`gods-eye-view/`** remains its own repo with its own remote. HELIX consumes it; it is
  not vendored into HELIX.
- **`.hermes/`** stays where the running services expect it.
- **Deep module structure.** `actions/`, `agents/`, `dashboard/`, `memory/` are not
  "unnecessary nesting" — they are the boundaries the modular monolith depends on.

## 6. Remaining structural debt

| Item | Why it stays | Suggested fix |
|---|---|---|
| `JARVIS/venv/` inside the repo root | Convenient, works | Acceptable; already untracked |
| `JARVIS/Jarvis/startup.log` | Diagnostic history | Add `Jarvis/` to `.gitignore` |
| `JARVIS/requirements*.txt` unpinned | Pre-existing | Pin after the next working install |
| `helix/consolidated_summary.md` at root | Stale narrative | Fold into `docs/` next pass |
