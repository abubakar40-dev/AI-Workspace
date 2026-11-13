# Canonical Memory Guarantees (evidence-based, 2026-11-11)

Sources: `AJ/aj/memory.py` (`MemoryPort`, `MemoryStore`), `aj/runtime.py`/`aj` checks, transfer/backup helpers, tests `tests/test_memory.py` and related suite coverage. Canonical store is provider-independent append-oriented event/record storage; Obsidian/Honcho are **not** canonical.

## Raw authoritative records
- **Architecture:** `MemoryStore` persists canonical memory events/records on disk (JSON/JSONL structures per implementation) and exposes append/record operations; summaries/indexes are derived/read models.
- **VERIFIED (baseline):** `aj --check` memory and summary checks pass; full suite green (217). Existing tests exercise memory persistence, summary/read behavior, and verification paths.
- **Guarantee intent:** append operations must not overwrite earlier authoritative raw events; summary generation must not modify raw event records.
- **VERIFICATION REQUIRED:** exhaustive failure-mode proofs (mid-write interruption, derived/index failure, provider/search unavailability) showing raw records remain intact and readable in all supported cases.

## Derived records and provenance
- **Architecture:** summaries/stats/search/index outputs are derived from canonical records; `MemoryPort` separates interface from store implementation.
- **VERIFIED (partial):** summaries can be generated and checked; transfer/verify tooling exists.
- **Guarantee intent:** derived records retain provenance to source canonical records; derived layers are rebuildable where supported; rebuilding must not duplicate or destroy authoritative events; derived-layer failure must not corrupt canonical records.
- **VERIFICATION REQUIRED:** explicit rebuild-from-raw tests, provenance-field completeness assertions, and isolation tests where index/summary generation fails after canonical append.

## Recovery, backup, restore
- **VERIFIED (baseline):** fresh-process checks via `aj --check`/runtime and persisted-store behavior pass in covered scenarios; incremental and campaign backups exist (`backups/f2_f4_incremental_20261111/`, `backups/f2f5_incremental_20261111b/`, prior checkpoint backup preserved).
- **Guarantee intent:** fresh process can read previously committed canonical events; backup/restore preserves required canonical records; integrity checks detect relevant corruption.
- **VERIFICATION REQUIRED:** isolated temporary-store tests for fresh-process reopen, backup/restore round-trip of canonical + required derived metadata, and corruption detection/recovery behavior under controlled faults. No migration/deletion/rewrite of existing user memory stores performed.


## F5 isolated proof tests (2026-11-11 continuation, temp stores only)

Evidence: `AJ/tests/test_f5_memory_proofs.py` (**7 passed**, isolated `tmp_path` stores only; no user memory store touched).

| Guarantee | Implementation / mechanism | Test | Method | Result | Limitation |
|---|---|---|---|---|---|
| Raw event preservation under derived summary failure | Canonical `raw_events` append-only; `summary.build` writes derived summary only | `test_raw_event_preservation_when_summary_generation_fails` | Append events, snapshot IDs/payloads/meta, force `add_summary` failure during `summary.build`, re-read and `verify()` | **VERIFIED (isolated):** raw snapshot unchanged, no delete/rewrite/duplication, `store.verify()` OK | Injected application-level failure; OS/power-loss mid-transaction not simulated |
| Derived/search read-path failure isolation | Search/FTS read path separate from canonical rows | `test_raw_event_preservation_when_search_fails` | Force `search()` failure after append, re-read canonical events | **VERIFIED (isolated):** raw events unchanged | Simulated read/search failure, not full index corruption/rebuild workflow |
| Derived isolation + rebuild without raw mutation | `summary.build/delete/verify`, summaries cite source event IDs | `test_derived_data_isolation_and_rebuild_without_raw_mutation` | Build summaries repeatedly, verify, delete derived summaries, rebuild, compare canonical snapshots/counts/content | **VERIFIED (isolated):** repeated generation did not duplicate raw events; delete removed derived only; rebuild produced same digest content; raw unchanged | Deterministic digest behavior as implemented; no external index provider |
| Provenance / citation integrity (supported fields) | Raw event fields (id/at/kind/source/task_id/content/meta), summary `source_event_ids`, kind, created_by/at | `test_summary_provenance_and_citation_integrity` | Append with task/source/meta, build summary, assert cited source IDs and retained raw provenance/metadata, `store.verify()` | **VERIFIED (supported fields):** citations and retained fields present; raw unchanged | Only fields supported by current schema/API asserted; no invented provenance fields |
| Fresh-process recovery | SQLite WAL-backed store reopened independently | `test_fresh_process_recovery_of_canonical_events` | Process A appends+closes temp DB; subprocess B reopens and reads events | **VERIFIED (isolated):** identities, content, timestamps, task/source/meta match after reopen | Same-host subprocess reopen; not kill-during-write at arbitrary WAL boundary |
| Backup + verification (original intact) | `transfer.backup_directory`, `transfer.verify_backup` on isolated config/store | `test_backup_and_verify_on_isolated_temp_store` | Populate temp canonical store, run backup, verify backup, compare original store after backup | **VERIFIED (isolated):** backup verified (`ok`, no problems) and original temp store unchanged | Full restore/import round-trip into separate runtime target not proven here beyond supported backup/verify; real-user stores not used |
| Corruption detection | `MemoryStore.verify()` / summary citation integrity checks | `test_corruption_detection_on_isolated_temp_store` | Inject invalid summary citation in disposable temp DB copy, run `verify()` | **VERIFIED (isolated):** `verify().ok == False` (corruption detected) | Detection only; automated repair/recovery semantics not proven; corruption limited to controlled citation case |

**Still VERIFICATION REQUIRED:** exhaustive mid-write/power-loss/raw-transaction interruption proofs, rebuild/index behavior for every derived artifact type, full restore/import correctness proofs for all store components beyond supported backup/verify path, and broader corruption classes.
