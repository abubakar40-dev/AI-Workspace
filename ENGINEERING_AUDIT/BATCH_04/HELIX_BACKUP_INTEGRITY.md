# HELIX Backup Integrity (Workstream C1)

**Existing backup (not modified):** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/backup/HELIX-backup-20261109T211343Z-batch03`  
**Source:** `/home/abubakargcx/helix` (dirty worktree preserved in backup; source unchanged during Batch 03/A4)  
**Verification outputs (separate, Batch 04):** `BATCH_04/helix_source.sha256`, `BATCH_04/helix_backup.sha256`

## Method (A4, non-destructive)
- Generated SHA256 manifests over **regular files** using `find -type f | LC_ALL=C sort | sha256sum` in both trees.
- Comparison scope aligned to Batch 03 documented exclusions: source manifest excluded `./ui/node_modules/*`, `*/__pycache__/*`, `*/.pytest_cache/*`, `*.pyc`; backup manifest excluded `*/__pycache__/*`, `*.pyc` (backup did not contain `ui/node_modules`).
- `.git` files were included in these manifests (as regular files under `.git`) — repository metadata covered in file-level hashing where present as files.
- No overwrite of existing backup; no modification of source.

## Results (VERIFIED for compared scope)
| Metric | Value |
|---|---|
| Source manifest entries | 808 |
| Backup manifest entries | 808 |
| `diff -q` result | **HASH_MATCH** |

## Excluded generated files (documented)
- `ui/node_modules/` — generated JS dependencies (excluded from backup and from source comparison). Reproducible if manifests (`package.json`/lockfile) preserved.
- `__pycache__/`, `.pytest_cache/`, `*.pyc` — generated caches/bytecode.

## Repository metadata
- `.git` directory contents were preserved by Batch 03 `rsync -a` and included in the file-level checksum pass (as applicable). No separate `git fsck` or pack verification was run.

## Restore test
- **Not performed** (would require a disposable copy workflow; Batch 04 did not create/modify a test restore target beyond verification outputs). A disposable restore test is permitted only if created separately without modifying existing source/backup — recommended in a later controlled step.

## Assessment
**Backup is suitable for recovery of preserved project files and worktree state (including untracked WIP and `.git` as preserved)** within the documented exclusion scope. Integrity is **cryptographically verified (SHA256 match)** for 808 compared files. Limitations: generated `node_modules` excluded; no full restore drill; no total-byte report captured in this pass.
