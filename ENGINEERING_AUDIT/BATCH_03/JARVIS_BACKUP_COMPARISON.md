# JARVIS Backup Comparison (Phase 6 / A1)

**Scope:** High-signal, read-only comparison of:
- `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/JARVIS-old-repo-20261106`
- `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/JARVIS-nested-duplicate-20261106`

**No merge/canonical selection. No file mutations.**

## Git/history (VERIFIED)
| Attribute | old-repo | nested-duplicate |
|---|---|---|
| Branch/status | `master`, dirty (mods/deletions visible) | same pattern observed |
| HEAD | `cffa32d30143023bc4086d8eb7f977a74fee7cdd` | same HEAD |
| Last commit | 2026-09-26 “Replace the Command Center with the ember/amber design” | same |
| Sampled counts (excl venv/.git) | py=15760, total=56940 | py=15760, total=56940 |

## Uniqueness/divergence (PARTIAL — comparison imperfect)
- A `comm -3` file-list comparison produced **sort warnings** and emitted a sample of differing paths (e.g., `chat_history/*`, `config/jarvis_browser_profile/*` runtime/profile artifacts). This indicates **possible divergence in runtime state, caches, profiles, chat history, or uncommitted artifacts**, but the method was **not a clean, fully sorted authoritative diff**.
- **Conclusion:** backups are **very similar by HEAD and coarse counts**, but **cannot be declared identical/duplicates** from this pass. Dirty working trees and runtime/profile directories may contain unique data.

## Preservation implication
Treat **both** as preservation candidates. Before any dedupe/canonical decision: generate a proper sorted manifest diff (excluding generated caches as appropriate, with documented rules), compare dirty deltas and unique source files, and obtain explicit user decision + GREEN SIGNAL for any move/delete.

## Active vs historical status
**UNVERIFIED.** `/home/abubakargcx/JARVIS` is missing and no runtime process was mapped to either backup path in this batch.
