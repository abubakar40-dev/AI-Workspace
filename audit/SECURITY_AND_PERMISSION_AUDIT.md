# Security and Permission Audit

Scope: JARVIS, HELIX, their bridge surfaces, credential handling, and the new
permission layer. Nothing in this document prints a secret value.

---

## 1. Findings summary

| ID | Severity | Finding | Status |
|---|---|---|---|
| S-1 | **High** | Bridge protocol had `confirm.request`/`confirm.response` that gated nothing; any tool could run without approval | **Fixed** — `core/confirmation.py` + `core/policy.py` |
| S-2 | **High** | `tools/lms_client.py` authenticates with a stored **password** and downloads are uncapped | Open — LMS workstream |
| S-3 | Medium | `bridge_ws.py` returns `Access-Control-Allow-Origin: *` | Open |
| S-4 | Medium | No audit trail for consequential actions | **Fixed** — `core/audit.py` (mode 0600, JSONL, redacted) |
| S-5 | Medium | Two dispatch paths, so a permission check in one is bypassed by the other | Partial — agent path gated, live path not |
| S-6 | Medium | `memory/personal_memory.sqlite3` is tracked in git | Open |
| S-7 | Low | HELIX voice modules each parsed the API key independently (3 copies) | **Fixed** — one `read_gemini_key` |
| S-8 | Low | `brahma_connect` pairing code (1,426 LOC) exposed a device gateway with no devices | **Removed** |
| S-9 | Low | Unpinned dependency manifests | Open |
| S-10 | Info | `helix` has a GitHub remote and no push was performed | Verified |

## 2. S-1 — the confirmation gate that gated nothing

Before this pass, the bridge defined `confirm.request` and `confirm.response` message
types, and no code consumed them. A consequential action requested over the bridge ran
immediately. This is worse than having no gate, because the protocol implied one existed.

Replacement, in `JARVIS/core/`:

- `capabilities.py` — every tool has a tier: `read`, `local-write`, `consequential`,
  `forbidden`. Per-action overrides (`file_controller: delete`, `browser_control:
  fill_form`). Unknown tools default to `local-write` and are audited as *unclassified*,
  so adding a tool cannot silently widen the consequential surface.
- `policy.py` — `allow` / `confirm` / `deny`. A `consequential` tier **without a token is
  denied**, not prompted-and-ignored.
- `confirmation.py` — a token is bound to `sha256(tool + canonical(args))`, single-use,
  expires in 300 s, in-process only (so a restart invalidates every approval).
- `audit.py` — one JSON line per action, `${XDG}/.local/share/jarvis/audit/actions-YYYY-MM.jsonl`,
  created `0600`, keys matching `token|password|secret|api_key|cookie|…` replaced with
  `[redacted]`, values truncated at 300 chars.

Verified behaviour (executed, `venv/bin/python`):

```
read          -> allow
consequential -> deny
with token    -> allow
replay        -> deny
payload swap  -> deny
```

And by `tests/test_core_policy.py` (11 tests): single-use, payload binding, tool binding,
expiry, unknown token, redaction, and "logging failure never breaks the caller".

**Limitation, stated plainly:** this gate is wired into `agent/executor.py::_call_tool`,
the agent path. The live Gemini dispatch chain in `main.py` is **not yet gated**. Until it
is, S-5 stands: a request that reaches the live chain skips policy.

## 3. S-2 — LMS credential model

`JARVIS/tools/lms_client.py` (12,292 B) logs in with `LMS_USERNAME` / `LMS_PASSWORD` from
the environment and posts to `/login/token.php`. Findings:

- Password auth where the site supports token auth. A token is revocable and scoped; a
  password is neither.
- The password is read from env, not a keyring. Anything that can read the process
  environment can read it.
- `download` has no size cap, so a hostile or accidental large resource exhausts disk.
- Uploads are draft-only today, which is the one good property.

Recommendation stands from the earlier investigation: **typed read-only Moodle REST first**,
with every write behind `core/confirmation` (course + action + target + expected effect in
the approved payload) and `core/audit` recording the attempt and the outcome. `quiz_attempt`
should be registered `forbidden` before any LMS write code is written — the capability
registry already supports that.

## 4. S-3 — CORS on a loopback bridge

`bridge_ws.py` sends `Access-Control-Allow-Origin: *`. It binds `127.0.0.1:8875`, so a
remote host cannot reach it, but *any page in the user's browser* can issue requests to it,
including a page the user did not write. Recommended: allowlist the dashboard origin and
require a per-session token. Not changed here because the dashboard and the mobile client
both depend on the current behaviour and I could not test either.

## 5. S-5 — the bypass, stated precisely

```
main.py dispatch chain A  ──► action functions          (no policy)   ← gap
agent/executor._call_tool ──► core.policy → action       (gated)      ← done
```

Two chains exist because the agent team and the live voice session were built at different
times. The fix is one call at the top of chain A, not a rewrite. It was not done in this
pass because the insertion point sits inside a 3,600-line async method and a bad edit there
breaks the assistant entirely; it is priority 2 in the final report.

## 6. S-6 — memory database in git

`memory/personal_memory.sqlite3` is tracked. It predates this audit. It contains personal
facts, not credentials, but it should not be in version control: every future commit
carries another copy, and history cannot be cleaned without a rewrite.

Recommended: `git rm --cached memory/personal_memory.sqlite3`, add to `.gitignore`, keep
the file on disk. **Not done here** because untracking user data is the owner's decision and
the file is genuinely the user's.

## 7. S-7 — key handling before and after

Before: `live_server.py`, `live_tts.py` and `helix_voice.py` each had their own regex over
`~/.hermes/.env`, and `helix_voice.py` also accepted a bare key file at
`/opt/helix-call/gemini.key`. Three parsers, three chances to leak in a log line.

After: `core/voice.py::read_gemini_key()` is the only parser. It never logs, accepts an
env var, a `KEY=value` file, or a bare key file, and returns the value only to its caller.
The `/opt/helix-call` path is still honoured (passed explicitly by `helix_voice`), so the
call box keeps working.

## 8. S-8 — what the Brahma removal took off the attack surface

Removed: a pairing/discovery gateway (1,426 LOC, 28 files) that listened on a port, stored
paired-device records with `cryptography`, and exposed `connect_execute` — a single entry
point that could run device actions by name. With no paired device, the only thing it could
still do was fail. Its config and device store were **moved to `backup/`**, so the pairing
keys are not destroyed, just out of the running tree.

## 9. Verified non-issues

| Check | Result |
|---|---|
| Secrets committed to either repo | **None.** Regex scan for `api_key|password|token = "<16+ chars>"` across tracked files: no hits. |
| `.env` tracked | No. |
| `config/api_keys.json` tracked | No. |
| Hermes `.env` read/copied | No — only parsed in memory by `read_gemini_key`. |
| Push to GitHub | **None.** `JARVIS` has no remote; `helix` remote untouched. |
| Credentials in this audit set | None. |
| `backup/` containing secrets | Yes — `smart_home.key` and `brahma_connect` device records are in `backup/removed-20261106/`. This is intentional (recovery path) but it means `backup/` must be treated as sensitive. |

## 10. Permission model as it now stands

| Tier | Meaning | Unattended? | Audited? |
|---|---|---|---|
| `read` | Observes only | Yes | Yes |
| `local-write` | Changes this machine, reversible | Yes | Yes |
| `consequential` | Outside the machine / irreversible / spends money | **No** — token required | Yes |
| `forbidden` | Never | Never | Yes (denied) |

The model is enforced in one place and is unit-tested. The remaining work is coverage, not
design.
