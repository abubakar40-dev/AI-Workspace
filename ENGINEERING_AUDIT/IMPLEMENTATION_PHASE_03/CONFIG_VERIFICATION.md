# Configuration Verification

## Inspection

`aj config` prints the effective configuration plus per-section origin:

```text
sources {'core': 'file', 'permissions': 'default', 'providers': 'file',
         'agents': 'default', 'capability': 'default', 'execution': 'default',
         'integrations': 'default', 'runtime': 'default',
         'feature_flags': 'default'}
```

Origins are `default`, `file`, `env` or `override`, tracked at section level.
Key-like configuration values are redacted through the same recursive redactor
used by export.

## Validation

`aj config --check` validates:

- `permissions.unattended_ceiling` is an integer in 0..2
- `permissions.approval_ttl_seconds` is a positive integer
- `core.data_dir` / `core.audit_dir` are non-empty and writable
- `providers.max_attempts` is an integer ≥ 1
- `execution.runtime` is `none` or `hermes`, with feature flags consistent
- required sections remain present

Invalid configuration exits 5:

```text
$ aj config --check          # ceiling 9
configuration: INVALID
  - permissions.unattended_ceiling must be an integer 0..2
exit 5
```

Ambiguity fixed during the phase: the subcommand's `--check` originally shared
the global health flag, causing `config --check` to run the full health suite.
The flag now has its own destination, so it validates only configuration.

**Result: PASS.**
