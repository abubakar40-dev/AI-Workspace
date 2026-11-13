# AJ Ecosystem Canonical Architecture v2

**Status:** proposed. Supersedes v1 (Batch 06) with corrected JARVIS and HELIX facts.
**Nothing here is implemented.** Each element carries an explicit reality label.

---

## 1. Status legend (apply to every box below)

| Label | Meaning |
|---|---|
| `RUNNING` | An active process/service exists and was observed |
| `SOURCE ONLY` | Code exists, no mapped runtime |
| `ACTIVE BRANCH` | Code exists on a consolidation branch, not on `main`/`master` |
| `CONTRACT ONLY` | Specification exists; no implementation |
| `NOT PROVEN` | Component exists but its key behaviour has never been demonstrated |
| `DEFERRED` | Deliberately postponed |

---

## 2. Target architecture

```text
                              USER
                               |
                               v
                    +----------------------+
                    |          AJ          |
                    | Control/Orchestration|
                    |  policy · tasks ·    |
                    |  audit · capabilities|
                    +----------+-----------+
                               |
        +----------------------+----------------------+
        |                      |                      |
        v                      v                      v
 +--------------+      +--------------+      +---------------+
 |   JARVIS     |      |    HELIX     |      |    HERMES     |
 |  Personal    |      |   Advanced   |      |  Workflow /   |
 |  Assistant   |      |  Execution   |      | Skill Runtime |
 +------+-------+      +------+-------+      +-------+-------+
        |                     |                      |
        +---------------------+----------------------+
                              |
                    +---------v----------+
                    | Provider Adapters  |
                    | router · health ·  |
                    | bounded fallback   |
                    +---------+----------+
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
  +-----------+        +-----------+        +-------------+
  | Provider A|        | Provider B|        | Local/Future|
  | OpenRouter|        | Anthropic/|        | stub/local  |
  | (verified)|        | Gemini …  |        | (none now)  |
  +-----------+        +-----------+        +-------------+
```

### 2.1 Reality check for that diagram

| Box | Actual state | Label |
|---|---|---|
| **AJ** | `AI_WORKSPACE/AJ`: 17 modules, contracts, 7 test files. **No git repo, no entrypoint, no process, tests never executed.** | `SOURCE ONLY` |
| **JARVIS** | `AI_WORKSPACE/JARVIS` @ `d93c702`, branch `audit/consolidation-2026-11-06`, 106 py files, 1.9 GB, policy/audit/confirmation core added, smart-home removed. Gateway unit inactive and pointing at a nonexistent path. | `ACTIVE BRANCH`, no runtime |
| **HELIX** | `AI_WORKSPACE/helix` @ `99c7a38`, branch `audit/consolidation-2026-11-06`, clean. `helix-live.service` active on `127.0.0.1:8788`; `helix-globe` active on `127.0.0.1:4173`. | **`RUNNING`** (voice proxy + globe only) |
| **Hermes** | Gateway PID 548124 active, WhatsApp bridge on `3000`, OpenRouter default. Honcho plugin enabled, **writer never proven**. | **`RUNNING`** |
| **Provider adapters** | Hermes routes to OpenRouter and is verified (`PONG`). AJ's `providers.py` is unexercised; no local provider exists. | Hermes `RUNNING`, AJ `SOURCE ONLY` |
| **AJ↔JARVIS / AJ↔HELIX / AJ↔Hermes links** | Contracts exist as dataclasses. **No transport, no adapter implementation, no call has ever been made.** | `CONTRACT ONLY` |

**The diagram is a target, not a description.** Today only three things actually run, and none of them talk to AJ — because AJ has no way to run.

---

## 3. Memory architecture

```text
                    AJ Memory Contract
                  (v1, specification)
                            |
                  +---------v----------+
                  |  CANONICAL RAW     |   append-only · provenance
                  |  events / tasks /  |   immutable · local disk
                  |  conversations     |   = the only real record
                  +---------+----------+
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
  +-----------+      +-------------+     +-------------+
  | Summaries |      |   Indexes   |     |  Adapters   |
  | cite raw  |      | lexical /   |     | replaceable |
  | ids       |      | semantic    |     |             |
  +-----------+      +-------------+     +------+------+
                                               |
                                        +------v------+
                                        |   HONCHO    |
                                        | candidate   |
                                        | adapter/    |
                                        | index only  |
                                        +-------------+
```

### 3.1 Reality check

| Layer | State | Label |
|---|---|---|
| Canonical raw | Designed in `aj/memory.py` (SQLite raw events + summaries citing ids). **Never executed.** | `CONTRACT ONLY` (design exists) |
| Summaries | Same module; no generator | `CONTRACT ONLY` |
| Indexes | None | `DEFERRED` |
| Honcho adapter | Honcho service healthy on PG18:5433, schema present, **`messages=0`, `conclusions=0` across every batch**, no proven writer | `NOT PROVEN` |
| Navigation (Obsidian) | Not part of any runtime | `DEFERRED` |

**Honcho is drawn as an adapter because that is all the evidence supports.** Two workspaces and one session exist from setup/API calls; not one message has ever been stored. Calling it canonical would be an assumption, not a finding.

---

## 4. Repository and identity boundaries

| Project | Source of truth | Branch state | Relationship |
|---|---|---|---|
| **AJ** | `AI_WORKSPACE/AJ` | no git | control plane; owns contracts and canonical memory |
| **JARVIS** | `AI_WORKSPACE/JARVIS` | `audit/consolidation-2026-11-06` @ `d93c702` (3 ahead of `master`); no remote | independent agent; personal-facing |
| **HELIX** | `AI_WORKSPACE/helix` | `audit/consolidation-2026-11-06` @ `99c7a38`; `main`/`origin/main` behind at `e8a64cf` | independent agent; advanced execution |
| **Hermes** | `~/.hermes` installation (external project) | vendored/installed, not part of these repos | workflow/skill runtime; not a memory owner |
| **Honcho** | `AI_WORKSPACE/honcho_local` + PG18 db `honcho` | service | candidate memory adapter |

**No merge is proposed anywhere.** The consolidation work already exists in each project's own audit branch; nothing is gained by combining them, and identity would be lost.

Note the shared pattern: HELIX and JARVIS both consolidated onto `audit/consolidation-2026-11-06` on the same day, with `main`/`master` left behind. That is a **branch-of-record policy** question (see `HELIX_WORKING_LINE_DECISION.md` §4.2), not a reason to merge.

---

## 5. Core infrastructure — where it lives

| Concern | Owner | Today |
|---|---|---|
| Configuration | AJ (`config.py`, layered) | static |
| Permissions | AJ (`permissions.py`, 5 levels + single-use approvals) | static |
| Audit | AJ (`audit.py`, JSONL, redaction) | static |
| Task lifecycle | AJ (`task.py`) | static |
| Capability registry | AJ (`capability.py`, `config/capabilities.json`) | static |
| Provider abstraction | AJ (`providers.py`) | static; Hermes routes independently |
| Memory interface | AJ (contract v1) | specification |
| Logging | per-component + AJ audit | fragmented |

**Duplication to watch:** JARVIS now carries its own `core/policy.py`, `core/audit.py`, `core/capabilities.py`, `core/confirmation.py`. That is a second policy engine beside AJ's. The ratified direction is that JARVIS *delegates* policy to AJ and keeps local checks only as a defence-in-depth cache — otherwise the audit trail splits in two.

---

## 6. Direction vs. implementation (do not conflate)

| Statement | Type |
|---|---|
| "AJ is the control plane" | **Approved direction (recommended, pending U2)** — not a running fact |
| "AJ owns canonical memory" | **Approved direction** — no storage exists |
| "Honcho is an adapter" | **Approved direction** — currently stores nothing |
| "JARVIS/HELIX/Hermes are independent projects" | **Evidence-established** — three separate trees/installations |
| "The four components are wired together" | **False today** — no AJ↔peer call has ever occurred |
| "The ecosystem is implemented" | **False** — one runtime (Hermes) + two HELIX UI services exist; the control plane does not run |

---

## 7. What v2 changes from v1

1. **JARVIS is no longer "backups only."** A live, committed, consolidated tree exists at `AI_WORKSPACE/JARVIS`; v1's framing was wrong.
2. **HELIX is no longer "two competing lines."** Line A *contains* Line B's head commit, and Line B's uncommitted work is 69/74 byte-identical to the checkpoint commit on Line A. This is a ref-topology question, not an architecture fork.
3. **No open architectural blocker remains in the HELIX or JARVIS identity questions** — only ratification and ref hygiene.
4. **The sole hard technical unknown is unchanged:** whether Hermes can write to Honcho at all. Every memory decision downstream of that remains provisional.
