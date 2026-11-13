# Next Phase

Phase 3 completes the local reliability core. Recommended Phase 4, still local:

1. **Retention and compaction** for `tasks.jsonl` and audit, preserving canonical
   raw memory and append-only audit history (snapshot + verified archive, never
   silent deletion).
2. **Cross-process operation lease** per task so concurrent cancel/retry cannot
   race, with an audited owner token.
3. **Richer lineage** for delegated child tasks (`parent_task_id` already exists)
   and a graph view that does not invent relationships.
4. **Backup encryption / secure export** if backups leave the machine; keep keys
   outside the repository.
5. **Config provenance per key**, and schema versioning for config files.
6. **Import merge policy** with explicit resolution for divergent task ids.
7. **Optional at-rest redaction review** for free-text task payloads.
8. Only after these: one external integration (starting with a read-only
   capability), still behind explicit permission and replay/retry declarations.

No external integration, GUI, voice, browser automation or LLM call is part of
Phase 4's local core work.
