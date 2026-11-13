# CLI Verification

## Commands exercised

`run`, `tasks`, `task`, `cancel`, `retry`, `audit`, `memory`, `summary`,
`capabilities`, `permissions`, `config`, `config --check`, `diagnostics`,
`export`, `import --dry-run`, `import`, `backup`, `backup --verify`, `recover`,
`--check`.

## Observed exit codes

| Case | Code |
|---|---|
| successful run / cancel / retry / queries | 0 |
| cancel of a completed task | 1 |
| unknown task | 4 |
| free-text shell goal (`rm -rf /`) | 4 |
| unsafe retry | 6 |
| invalid configuration | 5 |
| malformed `--input` JSON | 5 |
| argparse misuse | 2 |

## JSON mode

`test_cli_json_output_is_clean` runs nine inspection commands with `--json` and
parses stdout with `json`. No log line, ANSI escape or banner is mixed in.
Errors in JSON mode return one document with `ok: false` and an error code.

## Quiet / verbose

`--quiet` reduces `tasks` to `<id> <status>` and `run` to one line. `--verbose`
prints data/audit paths to stderr only.

## Honesty note

`--stdout` for humans is concise; warnings (malformed records) and errors go to
stderr. Human output is not claimed to be machine-parseable; use `--json`.

**Result: PASS.**
