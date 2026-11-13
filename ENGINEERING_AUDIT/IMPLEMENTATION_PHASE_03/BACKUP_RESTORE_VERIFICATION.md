# Backup / Restore Verification

## Export/import

- Deterministic JSON: sorted tasks, sorted keys, metadata and counts.
- Key-like fields redacted.
- Validation checks format, version, list shapes, duplicate task ids.
- Dry run validates and reports without creating files.
- Import refuses existing task ids before any write; skips duplicate memory
  signatures; appends audit; rebuilds summaries from raw events.
- Export/backup writes use temp file + flush + fsync + `os.replace`.

## Backup

`backup.json` plus `manifest.json` with SHA-256, byte count and counts.
`--verify` recomputes the hash and re-validates structure.

## Evidence

```text
export counts: {'tasks': 4, 'audit': 8, 'memory': 7, 'summaries': 1}
dry run: tasks 4, audit 8, memory 7, conflicts none
import:  tasks 4, audit 8, memory 7
restored diagnostics: tasks 4 audit 8 memory 7 malformed 0
backup: VALID
```

The automated test seeds state, backs up, removes only its temporary directory,
imports, then checks the task, audit and memory rows by task id. A separate test
appends one byte to `backup.json` and confirms `verify` reports invalid.

**Result: PASS.**
