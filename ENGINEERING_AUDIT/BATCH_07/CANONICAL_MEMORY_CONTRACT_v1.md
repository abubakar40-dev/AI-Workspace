# Canonical Memory Contract v1

**Status:** `RECOMMENDED` specification. Nothing implemented. Writing any of this into code = A3.

**Governing rule, stated once and assumed everywhere below:**

> **Derived memory must never silently replace or destroy canonical raw records.** Any layer that can be dropped and rebuilt from raw data is derived. Any layer whose loss is unrecoverable is canonical.

---

## 1. Why this contract exists

The ecosystem has four memory-shaped things that are easy to conflate:

| Thing | What it actually is today | Evidence |
|---|---|---|
| Hermes conversation history | Agent-local session state; not a shared memory | Active runtime, per-session logs |
| Honcho | A healthy PG18 backend with a schema, **0 messages, 0 conclusions**, and no proven writer | A2 counts unchanged B03→B07 |
| AJ `memory.py` | Raw-first append-oriented design with summaries citing raw IDs, SQLite draft | Static only, never executed |
| Obsidian-style notes | Human navigation layer, if/when used | Not part of any current runtime |

Three of these are frequently called "the memory." Only one is safe to call canonical, and only because of how it is *written*, not because of what it is called.

The decisive fact: **Honcho has never been observed to store a single message.** Two workspaces and one session exist from setup/API probing, but no message or conclusion row has ever appeared. A store that has never been written to cannot be canonical, regardless of how good its schema is.

---

## 2. Layer definitions (normative)

### 2.1 Canonical

**AJ-controlled raw event, task, and conversation records.**

| Property | Requirement |
|---|---|
| Ownership | AJ. No sub-agent writes canonical storage directly; agents submit records to AJ. |
| Form | Append-only. Corrections are new records referencing the corrected record — never in-place mutation. |
| Granularity | One row per discrete event: a message, a task transition, a tool invocation, a permission decision, a memory write refusal. |
| Content | Verbatim payload as produced, plus metadata. Not summarised, not paraphrased, not distilled. |
| Identity | Stable opaque id, monotonic creation timestamp, content hash of the payload. |
| Locality | Local disk, plain formats (SQLite + JSONL). Readable without the ecosystem running. |
| Loss semantics | **Unrecoverable if lost.** This is the only layer whose loss is a real loss. |

### 2.2 Derived

**Everything computed from canonical data.**

Summaries, embeddings, vector indexes, entity graphs, relevance scores, session digests, Honcho's own representations, model-generated "conclusions."

| Property | Requirement |
|---|---|
| Ownership | The layer's adapter. AJ owns only the *contract* and the rebuild command. |
| Rebuild | Must be fully reconstructible from canonical data plus a recorded adapter version. |
| Deletion | Safe to drop at any time. A dropped derived layer must degrade recall, never truth. |
| Provenance | Every derived artifact records the canonical ids it was computed from, plus model/adapter identifier and timestamp. |
| Authority | **None.** A derived artifact may never be cited as the record of what happened. |

### 2.3 Navigation

**Human-facing traversal.** Obsidian vaults, backlinks, tags, daily notes, wikilinks, dashboards.

| Property | Requirement |
|---|---|
| Ownership | The human. |
| Write direction | Generated from canonical/derived data; hand edits are their own artifact and must not be overwritten silently. |
| Authority | None over canonical records. A deleted note deletes a view, not an event. |
| Failure mode | Losing navigation costs convenience only. |

### 2.4 Adapter

**A replaceable implementation of a memory capability** — Honcho today as a candidate, something else tomorrow.

| Property | Requirement |
|---|---|
| Contract | Implemented against the AJ memory interface (interface 8 in `BATCH_07_LIMITED_FOUNDATION_PLAN.md`). |
| Storage | Owns its own schema. AJ never issues DDL against an adapter's database. |
| Declared capability | Must state what it provides: `write_raw`? `search_lexical`? `search_semantic`? `summarise`? `conclude`? |
| Degradation | Absence of an adapter must not break canonical writes. |
| Promotion | An adapter becomes *interesting* when proven; it never becomes canonical by adoption. |

---

## 3. Record schemas (conceptual, not code)

### 3.1 Common envelope — every canonical record

| Field | Type | Notes |
|---|---|---|
| `id` | opaque string | ULID/UUID; never reused |
| `kind` | enum | `conversation_message`, `task_event`, `tool_event`, `permission_event`, `system_event` |
| `created_at` | UTC timestamp, µs | Authoritative time; not the adapter's clock |
| `recorded_at` | UTC timestamp, µs | When AJ persisted it (detects backfill vs live) |
| `actor` | string | `user`, agent name (`jarvis`/`helix`/`hermes`), or `aj` |
| `session_id` | string or null | Conversation/session grouping |
| `task_id` | string or null | Links to the task ledger |
| `parent_id` | string or null | Causality: which record caused this one |
| `content_hash` | hex | Hash of payload for integrity/dedup |
| `payload` | object | Verbatim content |
| `provenance` | object | See 3.6 |
| `redaction` | object | See §6 |
| `schema_version` | integer | Contract version |

### 3.2 Conversation message

`role` (`user`/`assistant`/`system`/`tool`), `text` (verbatim), `attachments[]` (references, not blobs), `in_reply_to` (record id), `turn_index`.

### 3.3 Task event

`task_id`, `from_state` → `to_state`, `reason`, `assigned_agent`, `capability_ids[]`, `approval_ref` (id of the permission record that authorised it, if any).

### 3.4 Tool event

`tool_name`, `capability_id`, `invocation_args` (subject to redaction), `outcome` (`ok`/`error`/`denied`/`timeout`), `duration_ms`, `error_class`, `side_effects[]` (a *declaration* of what changed, e.g. `file_written:/path`, `call_placed:contact_ref`), `artifact_refs[]`.

Tool events matter disproportionately: they are the only durable answer to "what did the system actually do to the world."

### 3.5 Permission event

`subject` (actor), `action`, `capability_id`, `level`, `decision` (`granted`/`denied`/`expired`), `approval_id`, `single_use` (bool), `consumed_at`.

### 3.6 Provenance object — required on every record

| Field | Required | Notes |
|---|---|---|
| `producer` | yes | Component that originated the content (`hermes`, `jarvis`, `helix`, `aj.core`) |
| `producer_version` | yes | Commit short-sha or package version |
| `provider` | when applicable | `openrouter`, `anthropic`, `local`, `none` |
| `model` | when applicable | Exact model id as requested |
| `model_reported` | when applicable | Model id the provider reported back, if different |
| `prompt_ref` | when applicable | Record id of the prompt that produced this output |
| `adapter` | when written via one | Adapter name+version |
| `confidence` | optional | Only where a human/agent assertion is involved |

`provider`/`model` are mandatory for anything model-generated and forbidden from being inferred later — the whole point of provider independence is that you can still say *which* provider produced a given sentence.

---

## 4. Derived-layer contract

A derived artifact must carry: `derived_id`, `kind` (`summary`/`embedding`/`index_entry`/`conclusion`), `source_record_ids[]` (non-empty), `adapter`, `adapter_version`, `model`, `created_at`, `canonical_schema_version`.

**Invalid derived artifacts** — and the reason the rule at the top of this document exists:

| Anti-pattern | Why it is forbidden |
|---|---|
| A summary with no `source_record_ids` | Cannot be audited or corrected; becomes folklore |
| An embedding index as the only record of a conversation | Loss of index = loss of history |
| Honcho "conclusions" treated as ground truth about the user | Model inference promoted to fact without a raw basis |
| Summary written back over the raw record | Destroys evidence, silently |
| Deleting raw rows after summarising ("compaction") | The most common way memory systems lose their own history |

**Rebuild test (the acceptance criterion for the whole contract):** delete every derived layer, run rebuild, and recall must return to parity — with the same source ids. If rebuild cannot restore recall, something was canonical and mislabelled.

---

## 5. Retrieval

| Mode | Serves from | Notes |
|---|---|---|
| Exact lookup | Canonical | id, time range, session, task, actor, hash |
| Lexical search | Canonical (or a derived index with canonical fallback) | Must work with **zero** adapters present |
| Semantic search | Derived index | Optional; absence degrades quality, not availability |
| Recency/context assembly | Canonical | Deterministic ordering by `created_at`, then `id` |
| Cross-agent recall | Canonical, filtered by `actor`/`session_id` | Enables "what did HELIX do last Tuesday" |

**Ordering and windows must be deterministic** — same query, same result, independent of adapter state.

---

## 6. Redaction and secrets

Canonical records must be safe to keep forever.

| Rule | Implementation intent |
|---|---|
| Never store raw credentials | API keys, tokens, passwords, session cookies detected and replaced with `[[REDACTED:kind]]` **before** persistence |
| Redaction is recorded, not hidden | `redaction.applied=true`, `redaction.kinds[]`, `redaction.policy_version` |
| Redaction is not deletion | The record remains; the secret is absent |
| Personal content | Stored as given for the owner's own memory; never included in test payloads |
| Audit of access | Reads of canonical data by adapters are themselves auditable events |

---

## 7. Backup and recovery

| Layer | Responsibility | Minimum |
|---|---|---|
| Canonical | AJ | Nightly copy of SQLite + JSONL to a separate device/path; restore drill documented and **executed at least once** before the layer is trusted |
| Derived | Adapter owner | Optional; rebuildable, so backup is a convenience |
| Navigation | Human | Ordinary note backup |
| Contract | AJ | `schema_version` + migration notes; a canonical store must be readable by the next version |

**Recovery acceptance:** after restoring canonical data alone, lexical recall and full task history must work with no adapters installed.

---

## 8. Deletion policy

This is deliberately restrictive, because deletion is where memory contracts usually die.

| Request | Behaviour |
|---|---|
| Delete a derived artifact | Allowed, any time |
| Rebuild a derived layer | Allowed, any time |
| Delete a canonical record | **Denied by default.** Requires an explicit user-authorised purge operation, recorded as a `system_event` naming the record ids and the authority |
| Bulk delete / truncate | **Forbidden** as an unreviewed operation; no ad-hoc scripts, no manual `DELETE` |
| Retention expiry | Not implemented in v1. If ever added, expiry must be a declared policy with an auditable log, never silent |
| "Cleanup" after a test | Must never be improvised. Synthetic records are documented, not quietly removed |

A `system_event` recording a purge is itself canonical and must outlive the purge.

---

## 9. Auditability

Any claim about the past must be reconstructible:

1. **Who** — `actor`, `producer`, `producer_version`.
2. **What** — `kind`, `payload`, `content_hash`.
3. **When** — `created_at` (authoritative) and `recorded_at` (persistence).
4. **Why** — `parent_id` chain plus `approval_ref` for side-effecting acts.
5. **With what** — `provider`, `model`, adapter versions.
6. **Under which rules** — permission level, redaction policy version, schema version.

**Audit test:** given a task id, produce the full ordered chain (permission → dispatch → tool events → result → memory write), with providers/models named, without consulting any derived layer.

---

## 10. Responsibility summary

| Concern | Owner | Status |
|---|---|---|
| Canonical raw records | **AJ** | `RECOMMENDED`; design exists in `memory.py`, never executed |
| Raw-data custody/backup | **AJ** | `RECOMMENDED`; no backup exists yet |
| Summaries | AJ-governed contract, generator may be any adapter | `RECOMMENDED` |
| Embeddings / semantic index | Adapter (Honcho or other) | `DEFERRED` |
| Lexical search | Canonical store, adapter-optional | `RECOMMENDED` |
| Retrieval interface | **AJ** | `RECOMMENDED` |
| Honcho's role | Candidate adapter/index/derived service | `RECOMMENDED` — **not canonical** |
| Navigation layer | Human | `DEFERRED` |
| Migration/backfill | — | `DEFERRED`; depends on U1/U7 |

**Confidence: Medium-High.** The contract is sound and low-risk; the confidence ceiling comes from the fact that no AJ runtime exists to enforce it and no writer path into Honcho has ever been proven.
