# Security Verification

| Check | Result |
|---|---|
| Shell execution | Refused. `aj run "rm -rf /"` exits 4; only `echo …` maps internally |
| Arbitrary Python | No eval/exec path in `run`; only registered handlers |
| Unknown capability | Never executes; task fails with `capability_not_found` |
| External capability | Refused (`capability_unavailable`, exit 1) |
| Unsafe retry | Refused, exit 6, task marked for decision |
| Unsafe replay | `RECOVERY_REQUIRED`, no execution |
| Permission model | Inspection only; `aj permissions` cannot grant |
| Audit redaction | Key-like fields become `[redacted]` before persistence |
| Config redaction | Recursive key-based redaction; no provider credentials printed |
| Export redaction | Same recursive redactor applied before writing |
| Credentials | None stored or read; no network calls |

## Residual risk

Redaction is key-based. A secret pasted into task text or memory content is not
detected. Backups and exports are plaintext; they must be protected like the
store. These are documented limitations, not silently accepted behavior.

**Result: PASS.**
