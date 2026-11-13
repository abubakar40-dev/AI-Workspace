# Cleanup Plan (executed)

What was planned, what was actually done, and what was deliberately left.

---

## Stage 0 — Baseline (done)

| Recorded | Value |
|---|---|
| JARVIS branch / commit | `master` @ `cffa32d`, 133 dirty entries |
| helix branch / commit | `main` @ `e8a64cf`, 42 dirty entries |
| Test baseline | `509 passed, 2 failed` |
| Repos found | 4 (`JARVIS`, `helix`, `gods-eye-view`, `.hermes/hermes-agent`) + 1 nested duplicate |
| Duplicate trees | `JARVIS/JARVIS/` (1.5 G), `HERMES/` (6.3 G) |
| Services depending on these trees | `helix-globe`, `helix-live`, `hermes-gateway`, `oci-a1-launch` |

## Stage 1 — Recoverable checkpoint (done)

```
JARVIS  fe1f911  Checkpoint: pre-consolidation working state on an audit branch
helix   c68326b  Checkpoint: pre-consolidation working state on an audit branch
```

Both on new branch `audit/consolidation-2026-11-06`. Nothing pushed. Every uncommitted
change the owner had is now recoverable with `git checkout fe1f911` / `c68326b`.

## Stage 2 — Structural resolution (done)

| Action | Target |
|---|---|
| Moved | `JARVIS/JARVIS/` → `backup/JARVIS-nested-duplicate-20261106/` (1.5 G) |
| Moved | `HERMES/` → `backup/HERMES-workspace-duplicate-20261106/` (6.3 G) |

Moves were chosen over deletion because authority between the copies had not been proven
byte-for-byte. Both are recoverable with a single `mv`.

## Stage 3 — Brahma / Android removal (done)

Removed from the running tree, preserved in `backup/removed-20261106/`:

- `brahma_connect/` — 28 files, 1,426 lines
- `actions/brahma_connect.py` — 6 tools
- 6 declarations, 6 dispatch branches, 1 voice handler, 1 result narrator,
  1 startup block in `main.py` (**386 lines net**)
- the device branch in `file_controller.share_file`
- `config/brahma_connect.json`, `config/brahma_connect/`
- `tests/test_brahma_connect.py`, `tests/test_brahma_connect_actions.py`

## Stage 4 — Smart-home removal (done)

- `smart_home/` — 12 files, 1,588 lines
- its tool declaration, dispatch branch, handler, and the **per-utterance redirect**
- `config/smart_home.sqlite3`, `config/smart_home.key` (moved, **not** deleted)
- `python-kasa` from `requirements.txt` and `requirements-linux.txt`

## Stage 5 — Voice consolidation (done, structurally)

| Change | Detail |
|---|---|
| Created `JARVIS/core/voice.py` | model, voice, wake phrases, persona, sample rates, key lookup |
| HELIX `live_server.py` | imports the contract; **refuses to start** without it |
| HELIX `live_tts.py` | imports model, output rate, key |
| HELIX `helix_voice.py` | imports model, key; keeps `/opt/helix-call` key file |
| `helix/tools/check-live.py` | stale `gemini-3.8-live` → real model |
| `JARVIS/tools/` dedupe | 17 files, 1,995 lines of HELIX copies removed |

## Stage 6 — Foundational architecture (done, partially wired)

| Module | Purpose | Wired into |
|---|---|---|
| `core/capabilities.py` | tiers + per-action overrides + `forbidden` | `core/policy.py` |
| `core/policy.py` | allow / confirm / deny | `agent/executor._call_tool` |
| `core/confirmation.py` | single-use, payload-bound, 300 s TTL | `core/policy.py` |
| `core/audit.py` | JSONL, 0600, redacted | `agent/executor._call_tool` |
| `core/voice.py` | one voice contract | JARVIS + 3 HELIX transports |

**Not wired:** `main.py`'s live dispatch chain. Stated as an unresolved gap in the security
audit and the final report.

## Stage 7 — Bug fixes (done)

| Fix | File |
|---|---|
| LMS import path pointed one directory above the repo | `bridge_ws.py:302` |
| Duplicate voice config (3 → 1) | HELIX tools |
| Stale live model id in the diagnostic | `helix/tools/check-live.py` |
| `ui/node_modules` + `inbox/` committed to git | `helix/.gitignore` |

## Stage 8 — Validation (done)

| Check | Result |
|---|---|
| `pytest tests -q` (JARVIS) | **514 passed, 2 failed** (same 2 as baseline) |
| `py_compile` on every edited module | pass |
| HELIX voice modules compile | pass |
| `core.voice` resolves from `helix/tools` | pass |
| Policy behaviour (read / consequential / token / replay / payload-swap) | correct |
| Test count | 511 → 516 (6 Brahma tests out, 11 `core/` tests in) |

## Exact counts

| Metric | Count |
|---|---|
| Files relocated to `backup/removed-20261106/` | 44 (plus 2 config dirs) |
| Lines removed from tracked JARVIS source | **6,100** (4,105 + 1,995) |
| of which `main.py` | 386 |
| Duplicate trees relocated | 2 (7.8 G total) |
| Dependencies removed | 1 (`python-kasa`) |
| Commits created (JARVIS) | 3 (`fe1f911`, `6ba652b`, `d93c702`) |
| Commits created (helix) | 3 (`c68326b`, `07a2522` → `99c7a38`, `3d5929f`) |
| Pushes to GitHub | **0** |

## Deliberately NOT done

| Item | Reason |
|---|---|
| Delete any database, memory file or user document | Prohibited; smart-home and Brahma stores were moved instead |
| Gate `main.py`'s live dispatch chain | Insertion point inside a 3,600-line async method; needs a careful edit and a live test |
| Fix `_send_realtime` locking | Real concurrency fix; must be understood, not patched blind |
| Restore the boot greeting | Behaviour decision for the owner |
| Untrack `memory/personal_memory.sqlite3` | Owner's data; their call |
| Remove the Brahma-named UI strings | Cosmetic; changes a user-visible path |
| Reinstall / reconfigure Hermes | No need demonstrated |
| Add Docker, microservices, local LLM | Prohibited by the governing decisions |
