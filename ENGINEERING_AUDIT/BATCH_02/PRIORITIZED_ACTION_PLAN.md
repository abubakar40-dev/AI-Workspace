# Batch 02 Prioritized Action Plan (Top 15)

| ID | Action | Impact | Risk | Effort | Dependencies | Approval | Batchable |
|---|---|---|---|---:|---|---|---|
| P0-1 | **Preserve HELIX worktree**: approved non-destructive timestamped backup including untracked files | Prevents loss of WIP/untracked code/docs | Low if copy-only to safe target | M | disk space | **A4** | alone/first |
| P0-2 | **Map AJ/JARVIS runtime ownership**: launchers, systemd, shell/desktop/config refs → active repo/entrypoint | Resolves canonical identity blocker | Read-only | M | none | A1 | yes (read-only) |
| P0-3 | **Honcho DB metadata audit** (PG18:5433, `honcho` + other DBs): schemas/tables/row counts/timestamps, no content dumps | Confirms memory data owner | Low if read-only; access sensitive | M | admin access | **A2** | with P0-4 |
| P0-4 | **Trace Hermes→Honcho integration**: inspect `~/.hermes/plugins/honcho`, enablement, API usage; correlate with Honcho metadata | Confirms actual memory flow | Read-only | M | P0-3 helpful | A1 | yes |
| P0-5 | **Identify exposed unknown services** (8000, 8765) and confirm 3389/5432/5434 intent | Removes security unknowns | Read-only | S | none | A1 | yes |
| P1-6 | **HELIX refactor intent & feature map**: read build spec/progress/architecture, compare new bridge/UI to deleted paths | Safe recovery path | Read-only | M | P0-1 recommended | A1/user decision | yes |
| P1-7 | **Full diff JARVIS backup repos** (old vs nested) and classify unique dirty deltas | Prevents wrong dedupe/canonical pick | Read-only, I/O | M | none | A1 | yes |
| P1-8 | **Draft observed→target memory contract** (AJ canonical, Hermes operational, Honcho adapter?) with provenance/raw/retention | Architecture clarity | None (doc) | S | P0-3,P0-4,P0-2 | user review | yes |
| P1-9 | **Redacted full secret/config hygiene pass**: permissions (incl. honcho.json 664), exposure in code/log patterns, path drift (`JARVIS_ROOT`) | Reduces local risk | Read-only | S | none | A1 | yes |
| P1-10 | **Verify helix-globe/helix-live service health vs intended sources** (no restart) and document config paths | Confirms active HELIX-adjacent runtimes | Read-only | S | none | A1 | yes |
| P1-11 | **AJ foundation test/check plan** (isolated, no installs) — determine if stdlib tests runnable safely | Establishes AJ baseline | Low | S | P0-2 context | A1 | yes |
| P2-12 | **Backup/restore coverage inventory** for PG18 data dir and Docker volumes | Disaster readiness | Read-only | M | admin/path access | A1/A2 | later |
| P2-13 | **Harden exposure** (bindings/firewall/RDP/DB) after owner intent confirmed | Security improvement | Medium (ops) | M | P0-5 + decisions | **A3/GREEN SIGNAL** | controlled |
| P2-14 | **HELIX cleanup/restore/commit strategy** per file class | Repo health | High if wrong | M | P0-1,P1-6,user decision | **A3 + user decisions** | controlled |
| P2-15 | **Canonical repo consolidation/migration** (only after proof) | Long-term maintainability | High | L | P0-1,P0-2,P1-7,decisions | **A3 + user decisions** | staged |

**Safe to batch now (read-only, A1):** P0-2, P0-4 (partial), P0-5, P1-6, P1-7, P1-9, P1-10, P1-11. **Do first with approval:** P0-1 (backup copy), P0-3 (privileged DB metadata).
