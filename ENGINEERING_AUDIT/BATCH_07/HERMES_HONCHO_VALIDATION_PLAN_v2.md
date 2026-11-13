# Hermes → Honcho Validation Plan v2

**Status:** plan only. **Not executed.** Executing it requires `A3/GREEN SIGNAL` because every viable variant needs either a paid provider call or a configuration change.

---

## 1. Why Batch 06's test was invalid (root cause, precisely)

Batch 06 recorded a synthetic local turn with `msg='Reply with exactly: HONCHO_TEST_OK'` at `2026-11-10 00:25:38`. The agent log shows that turn was executed with:

```
provider=custom base_url=http://localhost:8123 model=gpt-6-astra
Streaming failed before delivery: Error code: 404 - {'detail': 'Not Found'}
```

Batch 07 found the matching configuration artefact: the `model:` block in `~/.hermes/config.yaml` still contains the comment **"Using local Honcho instance instead of OpenRouter"** directly under `provider: "openrouter"`. So at the time of that turn, Hermes was configured to treat **Honcho's memory API as an OpenAI-compatible LLM endpoint**. Honcho correctly returned 404 for `/chat/completions` and `/api/show`.

Consequences for the record:

| Aspect | Batch 06 state |
|---|---|
| Did a Hermes turn occur? | Yes |
| Did it reach an LLM? | No — it never completed a chat completion |
| Did it reach Honcho? | Yes, but as a **provider** endpoint, not a **memory** endpoint |
| Is that a writer test? | **No.** The memory hook is downstream of a completed turn |
| Honcho message delta | 0 (unchanged: `messages=0`) |

The turn therefore failed *before* the point where `sync_turn` is expected to run, which is exactly why no delta appeared. The 0-row result carries **no information** about the writer's correctness.

---

## 2. What must be true for a valid test

1. Hermes must complete a **real** model turn on a real provider route (so the turn lifecycle reaches its end).
2. Honcho must be reachable **only** as the memory target (`HONCHO_BASE_URL=http://localhost:8123`), never as `model.base_url`.
3. The payload must be synthetic, non-personal, non-production.
4. Pre/post inspection must be **metadata-only** (row counts + max timestamps), never message content.
5. Correlation must use request logs and timestamps, not payload dumps.
6. No cleanup may be improvised, and no `DELETE` may be issued.

Current blockers against (1):

| Route | Requires | Status |
|---|---|---|
| `openrouter/auto` (configured default) | A real API call charged to the user's OpenRouter account | **Paid call → A3 REQUIRED** |
| Any local model (Ollama/LM Studio/vLLM) | A listener that does not exist (no 11434/1234 listener; probe failed) plus a provider change | **Config mutation → A3 REQUIRED** |
| A stub/mock OpenAI-compatible server on loopback | Standing up a new local service and pointing Hermes at it | **Config mutation + new process → A3 REQUIRED** |

There is no fourth route. **The test cannot be performed under A1/A2/A4.**

---

## 3. Test design (approval-ready)

### 3.1 Variant selection (user picks one)

| Variant | Routing | Cost | Mutation | Notes |
|---|---|---|---|---|
| **V1 — Paid probe (cheapest)** | Keep `provider: openrouter`, `default: openrouter/auto`; one turn | one very short completion (fractions of a cent) | none | Least invasive; recommended if cost is acceptable |
| **V2 — Stub provider** | Temporarily set `model.base_url` to a loopback stub that returns a fixed short completion, then restore | none | temporary config edit + rollback | No external traffic; needs a stub process and a strict rollback step |
| **V3 — Local model** | Install/start a local OpenAI-compatible server, set provider | none (compute) | config edit + new service | Highest setup cost; not recommended for a one-question probe |

### 3.2 Preconditions checklist (all must pass before spending anything)

- [ ] `~/.hermes/config.yaml` backed up (as was done in the earlier router work) and its current `model:` block captured verbatim.
- [ ] Confirm `model.base_url` is **unset/absent** for the chosen variant (this is the exact defect that invalidated B06).
- [ ] Confirm `plugins.enabled` still contains `honcho`.
- [ ] Confirm `~/.hermes/honcho.json` points at `http://localhost:8123`.
- [ ] Confirm Honcho `/health`-equivalent responds on 8123 and PG18 on 5433 is accepting connections.
- [ ] Record the pre-test metadata snapshot (see 3.3).
- [ ] Note the Honcho server log offset (`wc -l` of the log) so post-test correlation window is exact.

### 3.3 Pre-test snapshot (metadata only)

```sql
select 'workspaces', count(*), coalesce(max(created_at)::text,'-') from workspaces
union all select 'sessions',  count(*), coalesce(max(created_at)::text,'-') from sessions
union all select 'peers',     count(*), coalesce(max(created_at)::text,'-') from peers
union all select 'messages',  count(*), coalesce(max(created_at)::text,'-') from messages
union all select 'conclusions', count(*), coalesce(max(created_at)::text,'-') from conclusions;
```

Current baseline (B07, unchanged since B03): `workspaces=2` (max `2026-11-09 23:10:54.276904`), `sessions=1` (max `2026-11-09 23:13:12.374012`), `peers=0`, `messages=0`, `conclusions=0`.

### 3.4 Synthetic interaction

Exactly one turn, synthetic identity, no personal content:

```
Reply with exactly: B07_SYNTHETIC_MEMORY_PROBE
```

Constraints: no real names, no credentials, no patient/health data, no project content, no file paths from the user's work, single turn, no tools, no attachments.

### 3.5 Observation window (read-only)

| Evidence | How | Content exposure |
|---|---|---|
| Hermes gateway log lines for the turn | `grep` on the synthetic marker only | the marker itself (synthetic) |
| Whether a Honcho request was issued | Honcho server log lines for the window | HTTP method + path only |
| Whether `sync_turn`/save ran | plugin debug lines if present, else absence is informative | none |
| Post-test metadata | same query as 3.3 | counts only |
| Process state | PIDs unchanged | none |

**Never** dump message bodies, never `select payload`/`content`, never print the Honcho API key.

### 3.6 Post-test comparison

Decision table:

| Honcho delta | Hermes log | Classification |
|---|---|---|
| `messages` +1 or more, timestamp advances | completed turn, Honcho `POST …/messages` in window | **`RUNTIME WRITER VERIFIED`** |
| `sessions`/`workspaces` advance but no message | completed turn, only session/workspace calls | **`PARTIALLY VERIFIED`** (lifecycle reached, message write did not) |
| no delta, but completed turn + Honcho requests present | write attempted and gated/failed | **`PARTIALLY VERIFIED`** → investigate gate |
| no delta and **no** Honcho requests | plugin not loaded or hook never ran | **`DISPROVEN` for this configuration** (writer path inactive) |
| turn did not complete (404/timeout/auth) | failed before lifecycle end | **`TEST INCONCLUSIVE`** — do not draw conclusions |

### 3.7 Cleanup

No manual deletion. If a delta occurs, the synthetic rows **stay**, and are documented as:

- workspace/session/peer/message/conclusion counts before and after,
- max timestamps after,
- the synthetic marker string,
- confirmation that no personal data was involved.

Any future removal requires a documented, tested, user-authorised purge — and per the memory contract, that purge must itself be recorded. Improvised `DELETE`/`TRUNCATE` is **not** authorized.

### 3.8 Rollback (V2/V3 only)

Restore the exact `config.yaml` captured in 3.2, verify `model.base_url` is absent again, and confirm one normal turn still routes to the intended provider. Rollback is a config mutation and is part of the same A3 authorization.

---

## 4. What this test can and cannot establish

**Can establish:** whether a completed Hermes turn produces an observable Honcho metadata delta consistent with the expected writer path — i.e. whether the integration is live at all.

**Cannot establish:** that Honcho is a suitable canonical store, that conclusions/summaries are correct, that multi-agent writes converge, or that the schema suits AJ's contract. Those are adapter-design questions, deliberately out of scope.

---

## 5. Classification of this plan

| Item | Label |
|---|---|
| Root-cause analysis of B06 failure | `EVIDENCE-ESTABLISHED` |
| Test design and decision table | `RECOMMENDED` |
| Executing V1 (paid call) | **`A3/GREEN SIGNAL REQUIRED`** |
| Executing V2/V3 (config mutation) | **`A3/GREEN SIGNAL REQUIRED`** + rollback authorisation |
| Any DB cleanup | **`A3/GREEN SIGNAL REQUIRED`**; not authorised now |
| Current writer status | **`TEST INCONCLUSIVE`** (unchanged by B07) |
