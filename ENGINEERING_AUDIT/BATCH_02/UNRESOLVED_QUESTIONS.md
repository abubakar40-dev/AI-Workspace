# Batch 02 Unresolved Questions

| ID | Question | Why unresolved | Safe next step | Approval |
|---|---|---|---|---|
| U01 | What is the canonical active AJ/JARVIS codebase and runtime entrypoint? | `/home/abubakargcx/JARVIS` missing; AJ foundation is non-git control-plane code; JARVIS backups are legacy/dirty/duplicate-by-HEAD sample; no runtime-to-repo mapping captured. | Read-only: map launchers/systemd/shell aliases/configs to absolute paths; full diff of backup repos; user clarification of intended active project. | None for read-only mapping; user decision required |
| U02 | Does Honcho’s PG18 `honcho` DB contain Hermes/AJ/JARVIS/HELIX data, and what is its schema? | TCP password auth blocked; no privileged socket query performed. | Admin-approved metadata-only inspection (tables/counts/timestamps/schemas), no message dumps. | Approved access method |
| U03 | Is Hermes actually writing to Honcho at runtime (and what data)? | Config/plugin present, service healthy; no runtime trace/log correlation captured. | Inspect `~/.hermes/plugins/honcho` and enabled config; controlled trace with explicit approval if it generates traffic. | A1/A2 depending |
| U04 | What owns externally bound ports 8000 and 8765? | PID/executable not fully resolved in this pass. | `lsof`/`/proc/<pid>/exe,cwd,cmdline,unit` correlation (read-only). | None |
| U05 | Is Docker Postgres (5432/5434) and GNOME RDP (3389) exposure intentional and protected? | Bindings observed; auth/firewall intent not audited. | Confirm product intent, auth config, firewall rules (read-only). Any bind/firewall change requires approval. | User/approval |
| U06 | What is HELIX’s intended architecture post-refactor (bridge/UI)? | Large deletions + untracked replacements; intent unknown. | Read HELIX build spec/progress/architecture docs and new bridge/UI files; user clarification. | User decision before restore/cleanup |
| U07 | Are God’s Eye View / Real-time News / Books of Eras / voice features preserved in current HELIX+services? | HELIX UI deletions observed; globe runs from `gods-eye-view` separately; feature mapping incomplete. | Feature-to-path/runtime map and safe validation in isolated copy. | A1 for safe tests |
| U08 | Where are other PG18 databases and who owns extra postgres process trees? | Full cluster inventory blocked. | Approved cluster metadata audit. | Approved access |
| U09 | Backup/restore coverage for PG18 Honcho data and Docker volumes? | Not verified. | Inventory backup jobs/snapshots; test restore in isolated environment. | Approval (restore tests) |
| U10 | Does AJ memory (`aj/memory.py`) run anywhere as canonical ecosystem memory? | Code exists; runtime/process/config linkage unknown. | Runtime-to-repo/config mapping and targeted code-path trace. | None/A1 |
