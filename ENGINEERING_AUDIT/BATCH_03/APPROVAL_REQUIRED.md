# Batch 03 — Approval Required (next steps)

**Executed under existing approval:** A1 read-only investigations, A2 metadata-only PG18/Honcho inspection (completed via local socket), A4 non-destructive HELIX backup. **No unrelated destructive ops performed.**

## Still requires explicit approval
| Item | Why | Scope |
|---|---|---|
| **Full SHA256 checksum manifest for HELIX backup** (optional hardening) | additional read/I/O; can be done read-only | A1/verification |
| **Privileged system-level owner identification for port 8000** if local `/proc` visibility insufficient | may require elevated inspection | A2/system read or approved method |
| **Any restore/cleanup/commit in HELIX or JARVIS backups** | state-changing; high preservation risk | A3/GREEN SIGNAL + user decisions |
| **Config/permission hardening** (e.g., `honcho.json` 600), firewall/bind changes | state-changing | A3/GREEN SIGNAL |
| **Honcho/Hermes backup or restore tests** | operational risk; must be isolated | approval |
| **Controlled Hermes→Honcho metadata-delta test** | creates test records/traffic (even if isolated) | explicit approval; metadata-only verification |
| **Canonical AJ/JARVIS source selection, migration, dedupe** | identity/data-risk decision | user decision + A3/GREEN SIGNAL |

## User decisions needed
- Intended canonical AJ runtime vs legacy JARVIS app; meaning of missing `/home/abubakargcx/JARVIS`.
- HELIX refactor intent (old bridge/UI restore vs new `bridge_ws.py`/`ui/src` completion).
- Exposure intent for 3389/5432/5434/8765/8000.
- Whether Honcho should become canonical memory adapter/store under AJ governance, based on observed schema/flows.
